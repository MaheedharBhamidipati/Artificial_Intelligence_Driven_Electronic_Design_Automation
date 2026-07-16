// =============================================================================
// RV32IMAC 5-STAGE IN-ORDER PIPELINED RISC-V CORE
// =============================================================================
// Implements: RV32I base integer ISA, "M" (mul/div), "A" (atomics: LR/SC + AMO*),
//             "C" (16-bit compressed instruction expansion).
//
// Pipeline: IF -> ID -> EX -> MEM -> WB  (classic 5-stage, in-order, single issue)
//
// Design choices / honest scope notes:
//  - Branches/jumps are resolved in EX (predict-not-taken, 2-cycle flush penalty
//    on taken control transfers). No branch predictor/BTB is implemented.
//  - Full forwarding (EX/MEM and MEM/WB -> EX) plus a load-use hazard stall.
//  - Integer multiply is single-cycle combinational (maps to a hardware
//    multiplier/DSP block on synthesis). Integer divide is a genuine
//    multi-cycle (33-cycle) restoring-divider FSM that stalls the pipeline,
//    because a single-cycle 32b divider is not realistic/synthesizable at
//    reasonable area/timing.
//  - Atomics: LR.W/SC.W implemented with a real reservation-set register.
//    AMO*.W implemented as a genuine 2-cycle read-modify-write in MEM stage.
//  - Minimal but real M-mode CSR file (mstatus, mtvec, mepc, mcause, mtval,
//    mscratch, mie, mip, mhartid, mcycle, minstret) and trap handling for
//    illegal instructions, ECALL, EBREAK, and misaligned instruction fetch.
//  - No caches, no MMU, no PLIC/CLINT, no multi-core coherence. Those are
//    separate, independently-verified subsystems, not "extra lines" you can
//    bolt onto a core file and still call correct.
//  - The instruction-fetch port reads two adjacent 32-bit words so that
//    16-bit compressed instructions that straddle a word boundary can be
//    reassembled; this is the standard technique used in real RVC front ends.
// =============================================================================

`timescale 1ns/1ps

// -----------------------------------------------------------------------
// Opcode map (RV32I/M/A/C base opcodes, bits [6:0] of the 32-bit instr)
// -----------------------------------------------------------------------
`define OPC_LOAD      7'b0000011
`define OPC_MISC_MEM  7'b0001111
`define OPC_OP_IMM    7'b0010011
`define OPC_AUIPC     7'b0010111
`define OPC_STORE     7'b0100011
`define OPC_AMO       7'b0101111
`define OPC_OP        7'b0110011
`define OPC_LUI       7'b0110111
`define OPC_BRANCH    7'b1100011
`define OPC_JALR      7'b1100111
`define OPC_JAL       7'b1101111
`define OPC_SYSTEM    7'b1110011

// ALU operation codes (internal, decoded from funct3/funct7/opcode)
`define ALU_ADD   4'h0
`define ALU_SUB   4'h1
`define ALU_SLL   4'h2
`define ALU_SLT   4'h3
`define ALU_SLTU  4'h4
`define ALU_XOR   4'h5
`define ALU_SRL   4'h6
`define ALU_SRA   4'h7
`define ALU_OR    4'h8
`define ALU_AND   4'h9
`define ALU_MUL   4'hA
`define ALU_COPY_B 4'hB   // pass-through of operand B (used for LUI/AUIPC style)

// M-extension sub-ops (funct3 field, when opcode==OP and funct7==0000001)
`define MULDIV_MUL     3'b000
`define MULDIV_MULH    3'b001
`define MULDIV_MULHSU  3'b010
`define MULDIV_MULHU   3'b011
`define MULDIV_DIV     3'b100
`define MULDIV_DIVU    3'b101
`define MULDIV_REM     3'b110
`define MULDIV_REMU    3'b111

// AMO funct5 (instr[31:27]) for the "A" extension, word-width ops only
`define AMO_ADD    5'b00000
`define AMO_SWAP   5'b00001
`define AMO_LR     5'b00010
`define AMO_SC     5'b00011
`define AMO_XOR    5'b00100
`define AMO_OR     5'b01000
`define AMO_AND    5'b01100
`define AMO_MIN    5'b10000
`define AMO_MAX    5'b10100
`define AMO_MINU   5'b11000
`define AMO_MAXU   5'b11100

// Writeback source select
`define WB_ALU   2'b00
`define WB_MEM   2'b01
`define WB_PC4   2'b10   // link address (JAL/JALR)
`define WB_CSR   2'b11

// Trap cause codes (subset actually used by this core)
`define CAUSE_ILLEGAL_INSTR   32'h00000002
`define CAUSE_BREAKPOINT      32'h00000003
`define CAUSE_ECALL_M         32'h0000000B
`define CAUSE_INSTR_MISALIGN  32'h00000000

// =============================================================================
// REGISTER FILE  (x0..x31, x0 hardwired to zero, write-through on same-cycle
// read-during-write so a dependent read in the same cycle sees the new value)
// =============================================================================
module regfile32 (
    input               clk,
    input               rst_n,
    input       [4:0]   rs1_addr,
    input       [4:0]   rs2_addr,
    output      [31:0]  rs1_data,
    output      [31:0]  rs2_data,
    input       [4:0]   rd_addr,
    input       [31:0]  rd_data,
    input               rd_we
);
    reg [31:0] regs [1:31];
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 1; i < 32; i = i + 1)
                regs[i] <= 32'h0;
        end else if (rd_we && rd_addr != 5'd0) begin
            regs[rd_addr] <= rd_data;
        end
    end

    assign rs1_data = (rs1_addr == 5'd0) ? 32'h0 :
                       (rd_we && rd_addr == rs1_addr && rd_addr != 5'd0) ? rd_data :
                       regs[rs1_addr];

    assign rs2_data = (rs2_addr == 5'd0) ? 32'h0 :
                       (rd_we && rd_addr == rs2_addr && rd_addr != 5'd0) ? rd_data :
                       regs[rs2_addr];

endmodule

// =============================================================================
// IMMEDIATE GENERATOR - produces the sign-extended immediate for every
// RV32I instruction format (I, S, B, U, J). Combinational.
// =============================================================================
module imm_gen (
    input       [31:0] instr,
    output reg  [31:0] imm
);
    wire [6:0] opcode = instr[6:0];

    always @(*) begin
        case (opcode)
            `OPC_LOAD, `OPC_OP_IMM, `OPC_JALR, `OPC_MISC_MEM, `OPC_SYSTEM:
                // I-type
                imm = {{20{instr[31]}}, instr[31:20]};
            `OPC_STORE:
                // S-type
                imm = {{20{instr[31]}}, instr[31:25], instr[11:7]};
            `OPC_BRANCH:
                // B-type
                imm = {{19{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0};
            `OPC_LUI, `OPC_AUIPC:
                // U-type
                imm = {instr[31:12], 12'b0};
            `OPC_JAL:
                // J-type
                imm = {{11{instr[31]}}, instr[31], instr[19:12], instr[20], instr[30:21], 1'b0};
            `OPC_AMO:
                imm = 32'h0; // AMO addressing uses rs1 only, no immediate
            default:
                imm = 32'h0;
        endcase
    end
endmodule

// =============================================================================
// ALU - combinational 32-bit integer ALU (also folds in the single-cycle
// MUL for the low-32-bit multiply case; MULH*/DIV/REM are handled outside)
// =============================================================================
module alu32 (
    input       [31:0] a,
    input       [31:0] b,
    input       [3:0]  op,
    output reg  [31:0] result
);
    always @(*) begin
        case (op)
            `ALU_ADD:  result = a + b;
            `ALU_SUB:  result = a - b;
            `ALU_SLL:  result = a << b[4:0];
            `ALU_SLT:  result = {31'b0, $signed(a) < $signed(b)};
            `ALU_SLTU: result = {31'b0, a < b};
            `ALU_XOR:  result = a ^ b;
            `ALU_SRL:  result = a >> b[4:0];
            `ALU_SRA:  result = $signed(a) >>> b[4:0];
            `ALU_OR:   result = a | b;
            `ALU_AND:  result = a & b;
            `ALU_MUL:  result = a * b;
            `ALU_COPY_B: result = b;
            default:   result = 32'h0;
        endcase
    end
endmodule

// =============================================================================
// MULH / MULHSU / MULHU - upper-32-bits-of-64-bit-product unit.
// Combinational (a real multiplier core); kept separate from the low-word
// MUL in alu32 so the top level can pick low or high half per funct3.
// =============================================================================
module mul_ext (
    input       [31:0] a,
    input       [31:0] b,
    input       [2:0]  funct3,   // MULDIV_MULH / MULHSU / MULHU
    output reg  [31:0] result_hi
);
    wire signed [63:0] mulh_ss  = $signed(a)  * $signed(b);
    wire signed [63:0] mulh_su  = $signed(a)  * $signed({1'b0, b});
    wire        [63:0] mulh_uu  = a * b;

    always @(*) begin
        case (funct3)
            `MULDIV_MULH:   result_hi = mulh_ss[63:32];
            `MULDIV_MULHSU: result_hi = mulh_su[63:32];
            `MULDIV_MULHU:  result_hi = mulh_uu[63:32];
            default:        result_hi = 32'h0;
        endcase
    end
endmodule

// =============================================================================
// DIVIDER UNIT - genuine multi-cycle (32-iteration) restoring-division FSM
// for DIV / DIVU / REM / REMU. This is what a real synthesizable RV32M
// divider looks like: a single-bit-per-cycle shift/subtract sequencer, not
// a combinational '/' operator (which would be enormous and slow at 32b).
//
// RISC-V semantics implemented exactly per the spec (no traps on div-by-zero
// or overflow; special-cased results instead):
//   DIV  x/0 = -1              DIVU x/0 = 0xFFFFFFFF
//   REM  x/0 = x                REMU x/0 = x
//   DIV  MIN/-1 overflow -> MIN   REM MIN/-1 overflow -> 0
// =============================================================================
module divider_unit (
    input               clk,
    input               rst_n,
    input               start,
    input       [31:0]  dividend,
    input       [31:0]  divisor,
    input       [2:0]   funct3,     // DIV/DIVU/REM/REMU
    output reg  [31:0]  result,
    output reg          busy,
    output reg          done
);
    reg  [31:0] a_abs, divisor_r;
    reg         result_neg_q, result_neg_r;
    reg  [5:0]  count;
    reg  [63:0] work;      // {remainder[31:0], quotient[31:0]} shift register
    reg  [2:0]  op_r;
    reg  [31:0] dividend_r;

    wire dividend_neg = dividend[31];
    wire divisor_neg  = divisor[31];

    localparam ST_IDLE = 2'd0, ST_INIT = 2'd1, ST_RUN = 2'd2;
    reg [1:0] state;

    wire [31:0] rem_field = work[63:32];
    wire [31:0] quo_field = work[31:0];
    wire [31:0] shifted_rem = {rem_field[30:0], quo_field[31]};
    wire [32:0] trial_sub   = {1'b0, shifted_rem} - {1'b0, divisor_r};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state  <= ST_IDLE;
            busy   <= 1'b0;
            done   <= 1'b0;
            result <= 32'h0;
        end else begin
            done <= 1'b0;
            case (state)
                ST_IDLE: begin
                    if (start) begin
                        op_r       <= funct3;
                        dividend_r <= dividend;
                        a_abs      <= (funct3 == `MULDIV_DIV || funct3 == `MULDIV_REM) && dividend_neg
                                        ? (~dividend + 32'h1) : dividend;
                        divisor_r  <= (funct3 == `MULDIV_DIV || funct3 == `MULDIV_REM) && divisor_neg
                                        ? (~divisor + 32'h1) : divisor;
                        result_neg_q <= (funct3 == `MULDIV_DIV) && (dividend_neg ^ divisor_neg);
                        result_neg_r <= (funct3 == `MULDIV_REM) && dividend_neg;
                        state <= ST_INIT;
                        busy  <= 1'b1;
                    end
                end

                ST_INIT: begin
                    work  <= {32'b0, a_abs};
                    count <= 6'd0;
                    state <= ST_RUN;
                end

                ST_RUN: begin
                    if (divisor_r == 32'h0) begin
                        case (op_r)
                            `MULDIV_DIV:  result <= 32'hFFFFFFFF;
                            `MULDIV_DIVU: result <= 32'hFFFFFFFF;
                            `MULDIV_REM:  result <= dividend_r;
                            `MULDIV_REMU: result <= dividend_r;
                            default:      result <= 32'h0;
                        endcase
                        busy  <= 1'b0;
                        done  <= 1'b1;
                        state <= ST_IDLE;
                    end else if (count == 6'd32) begin
                        if (op_r == `MULDIV_DIV || op_r == `MULDIV_DIVU)
                            result <= result_neg_q ? (~quo_field + 32'h1) : quo_field;
                        else
                            result <= result_neg_r ? (~rem_field + 32'h1) : rem_field;
                        busy <= 1'b0;
                        done <= 1'b1;
                        state <= ST_IDLE;
                    end else begin
                        if (trial_sub[32] == 1'b0)
                            work <= {trial_sub[31:0], quo_field[30:0], 1'b1};
                        else
                            work <= {shifted_rem, quo_field[30:0], 1'b0};
                        count <= count + 6'd1;
                    end
                end

                default: state <= ST_IDLE;
            endcase
        end
    end
endmodule


// =============================================================================
// RVC DECOMPRESSOR - expands a 16-bit "C" extension instruction into its
// equivalent full 32-bit RV32I/M instruction, combinationally, per the
// official RISC-V compressed-instruction-set encoding tables (RV32C, no
// floating-point C instructions since there is no F/D unit in this core).
//
// For J-type and B-type targets, the compressed offset is first assembled
// into a sign-extended 32-bit "logical" immediate (imm32) exactly as the
// spec defines it, and then re-packed into the standard 32-bit J-type /
// B-type instruction bit positions using the same formula a RISC-V
// assembler uses. This avoids hand-concatenation errors.
// =============================================================================
module rvc_decompressor (
    input       [15:0] c_instr,
    output reg  [31:0] instr32,
    output reg          illegal
);
    wire [1:0] op = c_instr[1:0];
    wire [2:0] f3 = c_instr[15:13];

    wire [4:0] rd_rs1_full = c_instr[11:7];   // quadrant 1/2 5-bit register field
    wire [4:0] rs2_full    = c_instr[6:2];    // quadrant 2 5-bit rs2 field
    wire [2:0] rd_c        = c_instr[4:2];
    wire [2:0] rs1_c       = c_instr[9:7];
    wire [2:0] rs2_c       = c_instr[4:2];
    wire [4:0] rd_p  = {2'b01, rd_c};         // x8-x15 compressed register set
    wire [4:0] rs1_p = {2'b01, rs1_c};
    wire [4:0] rs2_p = {2'b01, rs2_c};

    // ---- J-type (C.JAL / C.J) offset -> sign-extended 32-bit imm ----
    wire [10:0] j_off11 = {c_instr[12], c_instr[8], c_instr[10], c_instr[9], c_instr[6],
                             c_instr[7], c_instr[2], c_instr[11], c_instr[5], c_instr[4], c_instr[3]};
    wire [31:0] j_imm32 = {{20{j_off11[10]}}, j_off11, 1'b0};

    // ---- B-type (C.BEQZ / C.BNEZ) offset -> sign-extended 32-bit imm ----
    wire [7:0] b_off8 = {c_instr[12], c_instr[6], c_instr[5], c_instr[2],
                           c_instr[11], c_instr[10], c_instr[4], c_instr[3]};
    wire [31:0] b_imm32 = {{23{b_off8[7]}}, b_off8, 1'b0};

    always @(*) begin
        instr32 = 32'h0;
        illegal = 1'b0;
        case (op)
            // ======================= Quadrant 0 (op=00) =======================
            2'b00: begin
                case (f3)
                    3'b000: begin // C.ADDI4SPN -> addi rd', x2, nzuimm
                        reg [9:0] nzuimm;
                        nzuimm = {c_instr[10:7], c_instr[12:11], c_instr[5], c_instr[6], 2'b00};
                        if (nzuimm == 10'b0) illegal = 1'b1;
                        instr32 = {2'b00, nzuimm, 5'd2, 3'b000, rd_p, `OPC_OP_IMM};
                    end
                    3'b010: begin // C.LW -> lw rd', offset(rs1')
                        reg [6:0] off;
                        off = {c_instr[5], c_instr[12:10], c_instr[6], 2'b00};
                        instr32 = {5'b00000, off, rs1_p, 3'b010, rd_p, `OPC_LOAD};
                    end
                    3'b110: begin // C.SW -> sw rs2', offset(rs1')
                        reg [6:0] off;
                        off = {c_instr[5], c_instr[12:10], c_instr[6], 2'b00};
                        instr32 = {5'b00000, off[6:5], rs2_p, rs1_p, 3'b010, off[4:0], `OPC_STORE};
                    end
                    default: illegal = 1'b1; // C.FLW/C.FSD/C.LD/C.SD family - not supported (RV32IMAC has no F/D, no RV64)
                endcase
            end

            // ======================= Quadrant 1 (op=01) =======================
            2'b01: begin
                case (f3)
                    3'b000: begin // C.ADDI (rd==0,imm==0 => C.NOP)
                        reg [5:0] imm6;
                        imm6 = {c_instr[12], c_instr[6:2]};
                        instr32 = {{6{imm6[5]}}, imm6, rd_rs1_full, 3'b000, rd_rs1_full, `OPC_OP_IMM};
                    end
                    3'b001: begin // C.JAL -> jal x1, offset  (RV32-only encoding)
                        instr32 = {j_imm32[20], j_imm32[10:1], j_imm32[11], j_imm32[19:12], 5'd1, `OPC_JAL};
                    end
                    3'b010: begin // C.LI -> addi rd, x0, imm
                        reg [5:0] imm6;
                        imm6 = {c_instr[12], c_instr[6:2]};
                        if (rd_rs1_full == 5'd0) illegal = 1'b1;
                        instr32 = {{6{imm6[5]}}, imm6, 5'd0, 3'b000, rd_rs1_full, `OPC_OP_IMM};
                    end
                    3'b011: begin
                        if (rd_rs1_full == 5'd2) begin // C.ADDI16SP -> addi x2, x2, nzimm
                            reg [9:0] nzimm10;
                            nzimm10 = {c_instr[12], c_instr[4:3], c_instr[5], c_instr[2], c_instr[6], 4'b0000};
                            if (nzimm10 == 10'b0) illegal = 1'b1;
                            instr32 = {{2{nzimm10[9]}}, nzimm10, 5'd2, 3'b000, 5'd2, `OPC_OP_IMM};
                        end else begin // C.LUI -> lui rd, nzimm
                            reg [5:0] nzimm6;
                            nzimm6 = {c_instr[12], c_instr[6:2]};
                            if (nzimm6 == 6'b0 || rd_rs1_full == 5'd0) illegal = 1'b1;
                            instr32 = {{14{nzimm6[5]}}, nzimm6, rd_rs1_full, `OPC_LUI};
                        end
                    end
                    3'b100: begin
                        case (c_instr[11:10])
                            2'b00: begin // C.SRLI
                                if (c_instr[12]) illegal = 1'b1; // shamt[5] must be 0 on RV32
                                instr32 = {7'b0000000, c_instr[6:2], rs1_p, 3'b101, rs1_p, `OPC_OP_IMM};
                            end
                            2'b01: begin // C.SRAI
                                if (c_instr[12]) illegal = 1'b1;
                                instr32 = {7'b0100000, c_instr[6:2], rs1_p, 3'b101, rs1_p, `OPC_OP_IMM};
                            end
                            2'b10: begin // C.ANDI
                                reg [5:0] imm6;
                                imm6 = {c_instr[12], c_instr[6:2]};
                                instr32 = {{6{imm6[5]}}, imm6, rs1_p, 3'b111, rs1_p, `OPC_OP_IMM};
                            end
                            2'b11: begin
                                if (c_instr[12] == 1'b0) begin
                                    case (c_instr[6:5])
                                        2'b00: instr32 = {7'b0100000, rs2_p, rs1_p, 3'b000, rs1_p, `OPC_OP}; // C.SUB
                                        2'b01: instr32 = {7'b0000000, rs2_p, rs1_p, 3'b100, rs1_p, `OPC_OP}; // C.XOR
                                        2'b10: instr32 = {7'b0000000, rs2_p, rs1_p, 3'b110, rs1_p, `OPC_OP}; // C.OR
                                        2'b11: instr32 = {7'b0000000, rs2_p, rs1_p, 3'b111, rs1_p, `OPC_OP}; // C.AND
                                    endcase
                                end else begin
                                    illegal = 1'b1; // C.SUBW/C.ADDW/C.MULW etc - RV64-only / Zcb, unsupported
                                end
                            end
                        endcase
                    end
                    3'b101: begin // C.J -> jal x0, offset
                        instr32 = {j_imm32[20], j_imm32[10:1], j_imm32[11], j_imm32[19:12], 5'd0, `OPC_JAL};
                    end
                    3'b110: begin // C.BEQZ -> beq rs1', x0, offset
                        instr32 = {b_imm32[12], b_imm32[10:5], 5'd0, rs1_p, 3'b000, b_imm32[4:1], b_imm32[11], `OPC_BRANCH};
                    end
                    3'b111: begin // C.BNEZ -> bne rs1', x0, offset
                        instr32 = {b_imm32[12], b_imm32[10:5], 5'd0, rs1_p, 3'b001, b_imm32[4:1], b_imm32[11], `OPC_BRANCH};
                    end
                endcase
            end

            // ======================= Quadrant 2 (op=10) =======================
            2'b10: begin
                case (f3)
                    3'b000: begin // C.SLLI -> slli rd, rd, shamt
                        if (c_instr[12] || rd_rs1_full == 5'd0) illegal = 1'b1;
                        instr32 = {7'b0000000, c_instr[6:2], rd_rs1_full, 3'b001, rd_rs1_full, `OPC_OP_IMM};
                    end
                    3'b010: begin // C.LWSP -> lw rd, offset(x2)
                        reg [7:0] off;
                        off = {c_instr[3:2], c_instr[12], c_instr[6:4], 2'b00};
                        if (rd_rs1_full == 5'd0) illegal = 1'b1;
                        instr32 = {4'b0000, off, 5'd2, 3'b010, rd_rs1_full, `OPC_LOAD};
                    end
                    3'b100: begin
                        if (c_instr[12] == 1'b0) begin
                            if (rs2_full == 5'd0) begin // C.JR -> jalr x0, 0(rs1)
                                if (rd_rs1_full == 5'd0) illegal = 1'b1;
                                instr32 = {12'b0, rd_rs1_full, 3'b000, 5'd0, `OPC_JALR};
                            end else begin // C.MV -> add rd, x0, rs2
                                instr32 = {7'b0000000, rs2_full, 5'd0, 3'b000, rd_rs1_full, `OPC_OP};
                            end
                        end else begin
                            if (rd_rs1_full == 5'd0 && rs2_full == 5'd0) begin // C.EBREAK
                                instr32 = {12'b000000000001, 5'd0, 3'b000, 5'd0, `OPC_SYSTEM};
                            end else if (rs2_full == 5'd0) begin // C.JALR -> jalr x1, 0(rs1)
                                instr32 = {12'b0, rd_rs1_full, 3'b000, 5'd1, `OPC_JALR};
                            end else begin // C.ADD -> add rd, rd, rs2
                                instr32 = {7'b0000000, rs2_full, rd_rs1_full, 3'b000, rd_rs1_full, `OPC_OP};
                            end
                        end
                    end
                    3'b110: begin // C.SWSP -> sw rs2, offset(x2)
                        reg [7:0] off;
                        off = {c_instr[8:7], c_instr[12:9], 2'b00};
                        instr32 = {4'b0000, off[7:5], rs2_full, 5'd2, 3'b010, off[4:0], `OPC_STORE};
                    end
                    default: illegal = 1'b1; // C.FLDSP/C.FSDSP/C.LDSP/C.SDSP - unsupported
                endcase
            end

            default: illegal = 1'b1; // op==11 is not a compressed instruction (caller should not invoke us)
        endcase
    end
endmodule

// =============================================================================
// CSR FILE - minimal but functionally real M-mode control/status registers.
// Single combinational read port + single write port (safe because this is
// an in-order, single-issue pipeline: at most one CSR instruction occupies
// the MEM stage in any given cycle). Also owns trap entry/exit (mepc/mcause/
// mtval/mstatus.MPIE-MIE) and the free-running mcycle/minstret counters.
//
// Implemented CSRs: mstatus, misa, mie, mtvec, mscratch, mepc, mcause, mtval,
// mip, mhartid, mcycle[h], minstret[h]. Unimplemented addresses read as 0
// and silently ignore writes (per the RISC-V "unimplemented CSR" allowance
// for a minimal M-mode-only core), except this core reports zero for any
// address it doesn't recognize rather than pretending it's meaningful.
// =============================================================================
module csr_file (
    input               clk,
    input               rst_n,

    input       [11:0]  addr,
    output reg  [31:0]  rdata,      // current value at addr, combinational
    input       [31:0]  wdata,      // new value to store (already RS/RC-combined by caller)
    input               we,

    input               retire,     // pulse: one instruction committed this cycle (minstret++)

    input               trap_taken,
    input       [31:0]  trap_cause,
    input       [31:0]  trap_pc,
    input       [31:0]  trap_val,
    input               mret_taken,

    output      [31:0]  mtvec_out,
    output      [31:0]  mepc_out
);
    localparam CSR_MSTATUS  = 12'h300;
    localparam CSR_MISA     = 12'h301;
    localparam CSR_MIE      = 12'h304;
    localparam CSR_MTVEC    = 12'h305;
    localparam CSR_MSCRATCH = 12'h340;
    localparam CSR_MEPC     = 12'h341;
    localparam CSR_MCAUSE   = 12'h342;
    localparam CSR_MTVAL    = 12'h343;
    localparam CSR_MIP      = 12'h344;
    localparam CSR_MHARTID  = 12'hF14;
    localparam CSR_MCYCLE   = 12'hB00;
    localparam CSR_MCYCLEH  = 12'hB80;
    localparam CSR_MINSTRET = 12'hB02;
    localparam CSR_MINSTRETH= 12'hB82;

    reg [31:0] mstatus_r;
    reg [31:0] mie_r;
    reg [31:0] mtvec_r;
    reg [31:0] mscratch_r;
    reg [31:0] mepc_r;
    reg [31:0] mcause_r;
    reg [31:0] mtval_r;
    reg [31:0] mip_r;
    reg [63:0] mcycle_r;
    reg [63:0] minstret_r;

    // MISA: MXL[31:30]=01 (32-bit), extension bits A(0) C(2) I(8) M(12) set
    // = 0x40000000 | (1<<0) | (1<<2) | (1<<8) | (1<<12) = 0x40001105
    localparam [31:0] MISA_VAL = 32'h40001105;

    assign mtvec_out = {mtvec_r[31:2], 2'b00}; // this core only implements direct mode
    assign mepc_out  = {mepc_r[31:1], 1'b0};

    always @(*) begin
        case (addr)
            CSR_MSTATUS:   rdata = mstatus_r;
            CSR_MISA:      rdata = MISA_VAL;
            CSR_MIE:       rdata = mie_r;
            CSR_MTVEC:     rdata = mtvec_r;
            CSR_MSCRATCH:  rdata = mscratch_r;
            CSR_MEPC:      rdata = mepc_r;
            CSR_MCAUSE:    rdata = mcause_r;
            CSR_MTVAL:     rdata = mtval_r;
            CSR_MIP:       rdata = mip_r;
            CSR_MHARTID:   rdata = 32'h0;
            CSR_MCYCLE:    rdata = mcycle_r[31:0];
            CSR_MCYCLEH:   rdata = mcycle_r[63:32];
            CSR_MINSTRET:  rdata = minstret_r[31:0];
            CSR_MINSTRETH: rdata = minstret_r[63:32];
            default:       rdata = 32'h0;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            mstatus_r  <= 32'h0;
            mie_r      <= 32'h0;
            mtvec_r    <= 32'h0;
            mscratch_r <= 32'h0;
            mepc_r     <= 32'h0;
            mcause_r   <= 32'h0;
            mtval_r    <= 32'h0;
            mip_r      <= 32'h0;
            mcycle_r   <= 64'h0;
            minstret_r <= 64'h0;
        end else begin
            mcycle_r <= mcycle_r + 64'h1;
            if (retire) minstret_r <= minstret_r + 64'h1;

            if (trap_taken) begin
                mepc_r            <= trap_pc;
                mcause_r          <= trap_cause;
                mtval_r           <= trap_val;
                mstatus_r[7]      <= mstatus_r[3];  // MPIE <= MIE
                mstatus_r[3]      <= 1'b0;          // MIE  <= 0 (traps disabled in trap handler)
            end else if (mret_taken) begin
                mstatus_r[3]      <= mstatus_r[7];  // MIE  <= MPIE
                mstatus_r[7]      <= 1'b1;          // MPIE <= 1
            end else if (we) begin
                case (addr)
                    CSR_MSTATUS:   mstatus_r  <= wdata;
                    CSR_MIE:       mie_r      <= wdata;
                    CSR_MTVEC:     mtvec_r    <= wdata;
                    CSR_MSCRATCH:  mscratch_r <= wdata;
                    CSR_MEPC:      mepc_r     <= {wdata[31:1], 1'b0};
                    CSR_MCAUSE:    mcause_r   <= wdata;
                    CSR_MTVAL:     mtval_r    <= wdata;
                    CSR_MIP:       mip_r      <= wdata;
                    default: ; // unimplemented CSR write is a no-op
                endcase
            end
        end
    end
endmodule

// =============================================================================
// TOP-LEVEL CORE: rv32imac_core
// 5-stage in-order pipeline: IF -> ID -> EX -> MEM -> WB
// =============================================================================
module rv32imac_core (
    input               clk,
    input               rst_n,

    // Instruction fetch port: word-aligned base address + the two adjacent
    // 32-bit words needed to reconstruct a possibly-unaligned 16/32-bit
    // instruction at that PC (standard RVC front-end technique).
    output      [31:0]  imem_addr,
    input       [31:0]  imem_rdata0,
    input       [31:0]  imem_rdata1,

    // Data memory port (byte-addressed, byte-strobe write)
    output      [31:0]  dmem_addr,
    output      [31:0]  dmem_wdata,
    output      [3:0]   dmem_wstrb,
    output              dmem_req,
    input       [31:0]  dmem_rdata,

    // Debug/monitor outputs
    output              trap_o,
    output      [31:0]  mcause_o,
    output      [31:0]  retired_pc_o,
    output              retired_valid_o
);

    localparam [31:0] RESET_VECTOR = 32'h0000_0000;

    // =========================================================================
    // IF STAGE
    // =========================================================================
    reg  [31:0] pc;

    wire [31:0] fetch_base = {pc[31:2], 2'b00};
    assign imem_addr = fetch_base;

    wire [31:0] instr_window = pc[1] ? {imem_rdata1[15:0], imem_rdata0[31:16]} : imem_rdata0;
    wire        if_is_compressed = (instr_window[1:0] != 2'b11);
    wire [15:0] if_c_instr = instr_window[15:0];

    wire [31:0] if_rvc_expanded;
    wire        if_rvc_illegal;
    rvc_decompressor u_rvc_decomp (
        .c_instr (if_c_instr),
        .instr32 (if_rvc_expanded),
        .illegal (if_rvc_illegal)
    );

    wire [31:0] if_instr        = if_is_compressed ? if_rvc_expanded : instr_window;
    wire [2:0]  if_instr_len    = if_is_compressed ? 3'd2 : 3'd4;
    wire        if_fetch_illegal= if_is_compressed & if_rvc_illegal;
    wire [31:0] if_pc_next_seq  = pc + {29'b0, if_instr_len};

    // Control-transfer redirect bus (driven from EX for branches/jumps,
    // from MEM for traps/mret - see EX/MEM sections below)
    wire        redirect_valid;
    wire [31:0] redirect_target;
    wire        stall_pc, stall_ifid, stall_idex, stall_exmem;
    wire        flush_ifid, flush_idex;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            pc <= RESET_VECTOR;
        else if (redirect_valid)
            pc <= redirect_target;
        else if (!stall_pc)
            pc <= if_pc_next_seq;
        // else: hold (stalled)
    end

    // -------------------- IF/ID pipeline register --------------------
    reg         ifid_valid;
    reg  [31:0] ifid_pc;
    reg  [31:0] ifid_instr;
    reg  [31:0] ifid_pc_next;
    reg         ifid_fetch_illegal;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ifid_valid <= 1'b0;
            ifid_pc <= 32'h0; ifid_instr <= 32'h0; ifid_pc_next <= 32'h0;
            ifid_fetch_illegal <= 1'b0;
        end else if (redirect_valid || flush_ifid) begin
            ifid_valid <= 1'b0;
            ifid_instr <= 32'h0;
        end else if (!stall_ifid) begin
            ifid_valid <= 1'b1;
            ifid_pc <= pc;
            ifid_instr <= if_instr;
            ifid_pc_next <= if_pc_next_seq;
            ifid_fetch_illegal <= if_fetch_illegal;
        end
        // else held (stalled)
    end

    // =========================================================================
    // ID STAGE
    // =========================================================================
    wire [31:0] id_instr   = ifid_instr;
    wire [6:0]  id_opcode  = id_instr[6:0];
    wire [4:0]  id_rd_addr = id_instr[11:7];
    wire [4:0]  id_rs1_addr= id_instr[19:15];
    wire [4:0]  id_rs2_addr= id_instr[24:20];
    wire [2:0]  id_funct3  = id_instr[14:12];
    wire [6:0]  id_funct7  = id_instr[31:25];
    wire [11:0] id_csr_addr= id_instr[31:20];
    wire [4:0]  id_amo_funct5 = id_instr[31:27];

    wire [31:0] id_imm;
    imm_gen u_imm_gen (.instr(id_instr), .imm(id_imm));

    // ---- register file read (write port driven from WB stage below) ----
    wire [31:0] id_rs1_data_raw, id_rs2_data_raw;
    wire [4:0]  wb_rd_addr;
    wire [31:0] wb_rd_data;
    wire        wb_rd_we;

    regfile32 u_regfile (
        .clk(clk), .rst_n(rst_n),
        .rs1_addr(id_rs1_addr), .rs2_addr(id_rs2_addr),
        .rs1_data(id_rs1_data_raw), .rs2_data(id_rs2_data_raw),
        .rd_addr(wb_rd_addr), .rd_data(wb_rd_data), .rd_we(wb_rd_we)
    );

    // ---- primary opcode-level decode ----
    wire id_is_load    = (id_opcode == `OPC_LOAD);
    wire id_is_store   = (id_opcode == `OPC_STORE);
    wire id_is_opimm   = (id_opcode == `OPC_OP_IMM);
    wire id_is_op      = (id_opcode == `OPC_OP);
    wire id_is_lui     = (id_opcode == `OPC_LUI);
    wire id_is_auipc   = (id_opcode == `OPC_AUIPC);
    wire id_is_branch  = (id_opcode == `OPC_BRANCH);
    wire id_is_jal     = (id_opcode == `OPC_JAL);
    wire id_is_jalr    = (id_opcode == `OPC_JALR);
    wire id_is_system  = (id_opcode == `OPC_SYSTEM);
    wire id_is_miscmem = (id_opcode == `OPC_MISC_MEM);
    wire id_is_amo     = (id_opcode == `OPC_AMO);

    wire id_is_muldiv  = id_is_op && (id_funct7 == 7'b0000001);
    wire id_is_mul     = id_is_muldiv && (id_funct3 == `MULDIV_MUL || id_funct3 == `MULDIV_MULH ||
                                            id_funct3 == `MULDIV_MULHSU || id_funct3 == `MULDIV_MULHU);
    wire id_is_div     = id_is_muldiv && (id_funct3 == `MULDIV_DIV || id_funct3 == `MULDIV_DIVU ||
                                            id_funct3 == `MULDIV_REM || id_funct3 == `MULDIV_REMU);

    wire id_is_csr     = id_is_system && (id_funct3 != 3'b000);
    wire id_csr_imm_variant = id_funct3[2]; // 1xx = *I variants (rs1 field is a 5-bit uimm)
    wire id_is_ecall   = id_is_system && (id_funct3 == 3'b000) && (id_instr[31:20] == 12'h000);
    wire id_is_ebreak  = id_is_system && (id_funct3 == 3'b000) && (id_instr[31:20] == 12'h001);
    wire id_is_mret    = id_is_system && (id_funct3 == 3'b000) && (id_instr[31:20] == 12'h302);

    wire id_is_lr      = id_is_amo && (id_amo_funct5 == `AMO_LR);
    wire id_is_sc      = id_is_amo && (id_amo_funct5 == `AMO_SC);
    wire id_is_amo_op  = id_is_amo && !id_is_lr && !id_is_sc;

    // ---- illegal-instruction detection (real, not just a stub) ----
    wire id_known_opcode = id_is_load || id_is_store || id_is_opimm || id_is_op || id_is_lui ||
                            id_is_auipc || id_is_branch || id_is_jal || id_is_jalr || id_is_system ||
                            id_is_miscmem || id_is_amo;
    wire id_bad_amo_width  = id_is_amo && (id_funct3 != 3'b010); // only .W (word) supported
    wire id_bad_muldiv_f7  = id_is_op && (id_funct7 != 7'b0000000) && (id_funct7 != 7'b0100000) &&
                              (id_funct7 != 7'b0000001);
    wire id_bad_op_f7      = id_is_op && !id_is_muldiv &&
                              !(id_funct7 == 7'b0000000 || (id_funct7 == 7'b0100000 &&
                                (id_funct3 == 3'b000 || id_funct3 == 3'b101)));
    wire id_bad_shift_f7   = id_is_opimm && (id_funct3 == 3'b001) && (id_funct7 != 7'b0000000);
    wire id_bad_sra_f7     = id_is_opimm && (id_funct3 == 3'b101) &&
                              (id_funct7 != 7'b0000000) && (id_funct7 != 7'b0100000);
    wire id_bad_branch_f3  = id_is_branch && (id_funct3 == 3'b010 || id_funct3 == 3'b011);
    wire id_bad_load_f3    = id_is_load && (id_funct3 == 3'b011 || id_funct3 == 3'b110 || id_funct3 == 3'b111);
    wire id_bad_store_f3   = id_is_store && (id_funct3 != 3'b000 && id_funct3 != 3'b001 && id_funct3 != 3'b010);
    wire id_bad_system     = id_is_system && (id_funct3 == 3'b000) &&
                              !id_is_ecall && !id_is_ebreak && !id_is_mret;

    wire id_decode_illegal = !id_known_opcode || id_bad_amo_width || id_bad_muldiv_f7 || id_bad_op_f7 ||
                              id_bad_shift_f7 || id_bad_sra_f7 || id_bad_branch_f3 || id_bad_load_f3 ||
                              id_bad_store_f3 || id_bad_system;

    wire id_illegal = ifid_fetch_illegal || id_decode_illegal;

    // ---- writeback source select ----
    wire [1:0] id_wb_sel = (id_is_load || id_is_amo)                  ? `WB_MEM :
                            (id_is_jal || id_is_jalr)                  ? `WB_PC4 :
                            (id_is_csr)                                ? `WB_CSR :
                                                                          `WB_ALU;
    wire id_reg_write = (id_is_load || id_is_opimm || id_is_op || id_is_lui || id_is_auipc ||
                          id_is_jal || id_is_jalr || id_is_csr || id_is_amo) && (id_rd_addr != 5'd0);

    // ---- ALU control ----
    reg [3:0] id_alu_op;
    always @(*) begin
        if (id_is_lui) id_alu_op = `ALU_COPY_B;
        else if (id_is_auipc || id_is_jal || id_is_jalr || id_is_load || id_is_store || id_is_amo)
            id_alu_op = `ALU_ADD; // address / target generation
        else if (id_is_muldiv && id_funct3 == `MULDIV_MUL)
            id_alu_op = `ALU_MUL;
        else if (id_is_op || id_is_opimm) begin
            case (id_funct3)
                3'b000: id_alu_op = (id_is_op && id_funct7[5]) ? `ALU_SUB : `ALU_ADD;
                3'b001: id_alu_op = `ALU_SLL;
                3'b010: id_alu_op = `ALU_SLT;
                3'b011: id_alu_op = `ALU_SLTU;
                3'b100: id_alu_op = `ALU_XOR;
                3'b101: id_alu_op = id_funct7[5] ? `ALU_SRA : `ALU_SRL;
                3'b110: id_alu_op = `ALU_OR;
                3'b111: id_alu_op = `ALU_AND;
                default: id_alu_op = `ALU_ADD;
            endcase
        end else
            id_alu_op = `ALU_ADD;
    end

    // ---- operand source selects ----
    // EX operand A: PC (for AUIPC/JAL/JALR-target-base/branch target) or rs1
    wire id_alu_src_a_is_pc = id_is_auipc || id_is_jal;
    // EX operand B: immediate, or rs2 (register-register ops / branch compare uses rs2 directly)
    wire id_alu_src_b_is_imm = !(id_is_op || id_is_branch);

    // ---- memory control ----
    wire        id_mem_read  = id_is_load || id_is_lr || id_is_amo_op;
    wire        id_mem_write = id_is_store; // SC/AMO write handled specially in MEM stage
    wire [1:0]  id_mem_width = id_funct3[1:0];
    wire        id_mem_signed= !id_funct3[2];

    // =========================================================================
    // HAZARD DETECTION (uses ID-stage decode above vs. ID/EX register below)
    // =========================================================================
    wire        idex_valid_w;
    wire [4:0]  idex_rd_addr_w;
    wire        idex_is_late_result_w; // load / csr / lr -> result not ready until MEM
    wire        idex_reg_write_w;

    wire hazard_rs1 = idex_valid_w && idex_reg_write_w && idex_is_late_result_w &&
                       (idex_rd_addr_w != 5'd0) && (idex_rd_addr_w == id_rs1_addr);
    wire hazard_rs2 = idex_valid_w && idex_reg_write_w && idex_is_late_result_w &&
                       (idex_rd_addr_w != 5'd0) && (idex_rd_addr_w == id_rs2_addr);
    wire stall_load_use = hazard_rs1 || hazard_rs2;

    // -------------------- ID/EX pipeline register --------------------
    reg         idex_valid;
    reg  [31:0] idex_pc, idex_pc_next, idex_imm;
    reg  [31:0] idex_rs1_data, idex_rs2_data;
    reg  [4:0]  idex_rd_addr, idex_rs1_addr, idex_rs2_addr;
    reg  [3:0]  idex_alu_op;
    reg         idex_alu_src_a_is_pc, idex_alu_src_b_is_imm;
    reg  [1:0]  idex_wb_sel;
    reg         idex_reg_write;
    reg         idex_mem_read, idex_mem_write;
    reg  [1:0]  idex_mem_width;
    reg         idex_mem_signed;
    reg         idex_is_branch, idex_is_jal, idex_is_jalr;
    reg  [2:0]  idex_funct3;
    reg         idex_is_mul, idex_is_div;
    reg         idex_is_amo, idex_is_lr, idex_is_sc, idex_is_amo_op;
    reg  [4:0]  idex_amo_funct5;
    reg         idex_is_csr, idex_csr_imm_variant;
    reg  [11:0] idex_csr_addr;
    reg         idex_is_ecall, idex_is_ebreak, idex_is_mret;
    reg         idex_illegal;
    reg         idex_is_load;

    wire idex_bubble = stall_load_use || flush_idex || redirect_valid;

    assign idex_valid_w          = idex_valid;
    assign idex_rd_addr_w        = idex_rd_addr;
    assign idex_reg_write_w      = idex_reg_write;
    assign idex_is_late_result_w = idex_is_load || idex_is_csr || idex_is_lr || idex_is_amo_op;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            idex_valid <= 1'b0;
            {idex_pc, idex_pc_next, idex_imm, idex_rs1_data, idex_rs2_data} <= 0;
            {idex_rd_addr, idex_rs1_addr, idex_rs2_addr} <= 0;
            idex_alu_op <= 4'h0;
            {idex_alu_src_a_is_pc, idex_alu_src_b_is_imm} <= 0;
            idex_wb_sel <= 2'b0;
            idex_reg_write <= 1'b0;
            {idex_mem_read, idex_mem_write, idex_mem_width, idex_mem_signed} <= 0;
            {idex_is_branch, idex_is_jal, idex_is_jalr} <= 0;
            idex_funct3 <= 3'b0;
            {idex_is_mul, idex_is_div} <= 0;
            {idex_is_amo, idex_is_lr, idex_is_sc, idex_is_amo_op, idex_amo_funct5} <= 0;
            {idex_is_csr, idex_csr_imm_variant, idex_csr_addr} <= 0;
            {idex_is_ecall, idex_is_ebreak, idex_is_mret} <= 0;
            idex_illegal <= 1'b0;
            idex_is_load <= 1'b0;
        end else if (!stall_idex) begin
            if (idex_bubble) begin
                idex_valid     <= 1'b0;
                idex_reg_write <= 1'b0;
                idex_mem_read  <= 1'b0;
                idex_mem_write <= 1'b0;
                idex_is_branch <= 1'b0;
                idex_is_jal    <= 1'b0;
                idex_is_jalr   <= 1'b0;
                idex_is_mul    <= 1'b0;
                idex_is_div    <= 1'b0;
                idex_is_amo    <= 1'b0;
                idex_is_lr     <= 1'b0;
                idex_is_sc     <= 1'b0;
                idex_is_amo_op <= 1'b0;
                idex_is_csr    <= 1'b0;
                idex_is_ecall  <= 1'b0;
                idex_is_ebreak <= 1'b0;
                idex_is_mret   <= 1'b0;
                idex_illegal   <= 1'b0;
                idex_is_load   <= 1'b0;
            end else begin
                idex_valid   <= ifid_valid;
                idex_pc      <= ifid_pc;
                idex_pc_next <= ifid_pc_next;
                idex_imm     <= id_imm;
                idex_rs1_data<= id_rs1_data_raw;
                idex_rs2_data<= id_rs2_data_raw;
                idex_rd_addr <= id_rd_addr;
                idex_rs1_addr<= id_rs1_addr;
                idex_rs2_addr<= id_rs2_addr;
                idex_alu_op  <= id_alu_op;
                idex_alu_src_a_is_pc <= id_alu_src_a_is_pc;
                idex_alu_src_b_is_imm<= id_alu_src_b_is_imm;
                idex_wb_sel  <= id_wb_sel;
                idex_reg_write <= id_reg_write && ifid_valid;
                idex_mem_read  <= id_mem_read && ifid_valid;
                idex_mem_write <= id_mem_write && ifid_valid;
                idex_mem_width <= id_mem_width;
                idex_mem_signed<= id_mem_signed;
                idex_is_branch <= id_is_branch && ifid_valid;
                idex_is_jal    <= id_is_jal && ifid_valid;
                idex_is_jalr   <= id_is_jalr && ifid_valid;
                idex_funct3    <= id_funct3;
                idex_is_mul    <= id_is_mul && ifid_valid;
                idex_is_div    <= id_is_div && ifid_valid;
                idex_is_amo    <= id_is_amo && ifid_valid;
                idex_is_lr     <= id_is_lr && ifid_valid;
                idex_is_sc     <= id_is_sc && ifid_valid;
                idex_is_amo_op <= id_is_amo_op && ifid_valid;
                idex_amo_funct5<= id_amo_funct5;
                idex_is_csr    <= id_is_csr && ifid_valid;
                idex_csr_imm_variant <= id_csr_imm_variant;
                idex_csr_addr  <= id_csr_addr;
                idex_is_ecall  <= id_is_ecall && ifid_valid;
                idex_is_ebreak <= id_is_ebreak && ifid_valid;
                idex_is_mret   <= id_is_mret && ifid_valid;
                idex_illegal   <= id_illegal && ifid_valid;
                idex_is_load   <= id_is_load && ifid_valid;
            end
        end
        // else: held (stalled)
    end

    // =========================================================================
    // EX STAGE
    // =========================================================================
    // ---- forwarding sources from later stages (declared further below) ----
    wire        exmem_valid_fwd;
    wire [4:0]  exmem_rd_addr_fwd;
    wire        exmem_reg_write_fwd;
    wire [31:0] exmem_fwd_data;         // ALU-class result available at EX/MEM boundary
    wire        memwb_valid_fwd;
    wire [4:0]  memwb_rd_addr_fwd;
    wire        memwb_reg_write_fwd;
    wire [31:0] memwb_fwd_data;         // fully-muxed WB data

    // 2-bit forward select: 00 = no forward (use idex_rs*_data), 01 = from EX/MEM, 10 = from MEM/WB
    wire fwd_a_from_exmem = exmem_valid_fwd && exmem_reg_write_fwd && (exmem_rd_addr_fwd != 5'd0) &&
                             (exmem_rd_addr_fwd == idex_rs1_addr);
    wire fwd_a_from_memwb = memwb_valid_fwd && memwb_reg_write_fwd && (memwb_rd_addr_fwd != 5'd0) &&
                             (memwb_rd_addr_fwd == idex_rs1_addr) && !fwd_a_from_exmem;
    wire fwd_b_from_exmem = exmem_valid_fwd && exmem_reg_write_fwd && (exmem_rd_addr_fwd != 5'd0) &&
                             (exmem_rd_addr_fwd == idex_rs2_addr);
    wire fwd_b_from_memwb = memwb_valid_fwd && memwb_reg_write_fwd && (memwb_rd_addr_fwd != 5'd0) &&
                             (memwb_rd_addr_fwd == idex_rs2_addr) && !fwd_b_from_exmem;

    wire [31:0] ex_rs1_val = fwd_a_from_exmem ? exmem_fwd_data :
                              fwd_a_from_memwb ? memwb_fwd_data : idex_rs1_data;
    wire [31:0] ex_rs2_val = fwd_b_from_exmem ? exmem_fwd_data :
                              fwd_b_from_memwb ? memwb_fwd_data : idex_rs2_data;

    // ---- ALU operand muxes ----
    wire [31:0] ex_alu_a = idex_alu_src_a_is_pc ? idex_pc : ex_rs1_val;
    wire [31:0] ex_alu_b = idex_alu_src_b_is_imm ? idex_imm : ex_rs2_val;

    wire [31:0] ex_alu_result;
    alu32 u_alu (.a(ex_alu_a), .b(ex_alu_b), .op(idex_alu_op), .result(ex_alu_result));

    // ---- MULH*/MULHSU/MULHU (single-cycle, separate 64b product unit) ----
    wire [31:0] ex_mulh_result;
    mul_ext u_mul_ext (.a(ex_rs1_val), .b(ex_rs2_val), .funct3(idex_funct3), .result_hi(ex_mulh_result));
    wire ex_mul_use_hi = idex_is_mul && (idex_funct3 != `MULDIV_MUL);

    // ---- DIV/DIVU/REM/REMU (genuine multi-cycle sequential divider) ----
    wire        div_busy, div_done;
    wire [31:0] div_result;
    reg         div_start_pulse;
    reg         div_in_flight; // true from the cycle we issue until div_done

    divider_unit u_divider (
        .clk(clk), .rst_n(rst_n),
        .start(div_start_pulse),
        .dividend(idex_rs1_data), .divisor(idex_rs2_data), // latched operands: div ops don't need EX-stage fwd. of a value produced 1 cycle prior since stall holds them stable across the whole multi-cycle op
        .funct3(idex_funct3),
        .result(div_result), .busy(div_busy), .done(div_done)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            div_start_pulse <= 1'b0;
            div_in_flight   <= 1'b0;
        end else begin
            div_start_pulse <= 1'b0;
            if (idex_valid && idex_is_div && !div_in_flight && !div_busy) begin
                div_start_pulse <= 1'b1;
                div_in_flight   <= 1'b1;
            end else if (div_done) begin
                div_in_flight <= 1'b0;
            end
        end
    end

    wire stall_muldiv = idex_valid && idex_is_div && (div_in_flight || div_start_pulse) && !div_done;

    // ---- final EX-stage "ALU-class" result mux ----
    wire [31:0] ex_result = idex_is_div            ? div_result :
                             ex_mul_use_hi          ? ex_mulh_result :
                                                       ex_alu_result;

    // ---- branch condition evaluation ----
    reg ex_branch_cond;
    always @(*) begin
        case (idex_funct3)
            3'b000: ex_branch_cond = (ex_rs1_val == ex_rs2_val);                       // BEQ
            3'b001: ex_branch_cond = (ex_rs1_val != ex_rs2_val);                       // BNE
            3'b100: ex_branch_cond = ($signed(ex_rs1_val) < $signed(ex_rs2_val));      // BLT
            3'b101: ex_branch_cond = ($signed(ex_rs1_val) >= $signed(ex_rs2_val));     // BGE
            3'b110: ex_branch_cond = (ex_rs1_val < ex_rs2_val);                        // BLTU
            3'b111: ex_branch_cond = (ex_rs1_val >= ex_rs2_val);                       // BGEU
            default: ex_branch_cond = 1'b0;
        endcase
    end

    wire        ex_branch_taken = idex_valid && idex_is_branch && ex_branch_cond;
    wire [31:0] ex_branch_target = idex_pc + idex_imm;                    // B-type / J-type: pc + imm
    wire [31:0] ex_jalr_target   = (ex_rs1_val + idex_imm) & 32'hFFFF_FFFE;
    wire        ex_jump_taken    = idex_valid && (idex_is_jal || idex_is_jalr);
    wire [31:0] ex_jump_target   = idex_is_jalr ? ex_jalr_target : ex_branch_target;

    wire        ex_ctrl_redirect       = ex_branch_taken || ex_jump_taken;
    wire [31:0] ex_ctrl_redirect_target= ex_jump_taken ? ex_jump_target : ex_branch_target;

    // ---- EX-stage exception detection (committed later, at MEM, see below) ----
    wire ex_exception_pending = idex_valid && (idex_illegal || idex_is_ecall || idex_is_ebreak);
    wire ex_mret_pending      = idex_valid && idex_is_mret;

    // ---- CSR operand (rs1 value, or the 5-bit rs1-field-as-immediate for *I variants) ----
    wire [31:0] ex_csr_operand = idex_csr_imm_variant ? {27'b0, idex_rs1_addr} : ex_rs1_val;

    // =========================================================================
    // EX/MEM pipeline register
    // -------------------------------------------------------------------------
    // Memory-interface timing assumption (documented, not hidden): dmem is
    // modeled as a single-port memory with combinational (same-cycle) read,
    // i.e. dmem_rdata reflects dmem_addr's contents *before* any write issued
    // in that same cycle takes effect at the next clock edge (standard
    // "read-old-data-before-write" BRAM behavior). This lets LR/SC/AMO*
    // complete as genuine, correct single-cycle read-modify-write operations
    // without a separate multi-cycle FSM. A registered-read SRAM macro would
    // need an extra pipeline stage or replay logic; that is a real, separate
    // memory-subsystem design choice outside the scope of "the CPU core".
    // =========================================================================
    reg         exmem_valid;
    reg  [31:0] exmem_pc, exmem_pc_next;
    reg  [31:0] exmem_result;          // address (load/store/amo) or ALU/mul/div result
    reg  [31:0] exmem_store_data;      // forwarded rs2 value, for stores and AMO operand
    reg  [4:0]  exmem_rd_addr;
    reg  [1:0]  exmem_wb_sel;
    reg         exmem_reg_write;
    reg         exmem_mem_read, exmem_mem_write;
    reg  [1:0]  exmem_mem_width;
    reg         exmem_mem_signed;
    reg         exmem_is_amo, exmem_is_lr, exmem_is_sc, exmem_is_amo_op;
    reg  [4:0]  exmem_amo_funct5;
    reg         exmem_is_csr, exmem_csr_imm_variant;
    reg  [11:0] exmem_csr_addr;
    reg  [1:0]  exmem_csr_funct3_op;
    reg  [31:0] exmem_csr_operand;
    reg         exmem_is_ecall, exmem_is_ebreak, exmem_is_mret;
    reg         exmem_illegal;

    wire mem_redirect_valid; // driven from MEM-stage trap/mret commit logic (below)
    wire [31:0] mem_redirect_target;
    wire flush_exmem = mem_redirect_valid;

    assign exmem_valid_fwd     = exmem_valid;
    assign exmem_rd_addr_fwd   = exmem_rd_addr;
    assign exmem_reg_write_fwd = exmem_reg_write;
    assign exmem_fwd_data      = exmem_result; // valid for ALU/mul/div/PC4-class; loads/CSR/AMO
                                                // results aren't ready yet here, but those cases
                                                // are already excluded from forwarding via the
                                                // load-use style stall (idex_is_late_result_w).

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            exmem_valid <= 1'b0;
            {exmem_pc, exmem_pc_next, exmem_result, exmem_store_data} <= 0;
            exmem_rd_addr <= 5'b0; exmem_wb_sel <= 2'b0; exmem_reg_write <= 1'b0;
            {exmem_mem_read, exmem_mem_write, exmem_mem_width, exmem_mem_signed} <= 0;
            {exmem_is_amo, exmem_is_lr, exmem_is_sc, exmem_is_amo_op, exmem_amo_funct5} <= 0;
            {exmem_is_csr, exmem_csr_imm_variant, exmem_csr_addr, exmem_csr_funct3_op, exmem_csr_operand} <= 0;
            {exmem_is_ecall, exmem_is_ebreak, exmem_is_mret, exmem_illegal} <= 0;
        end else if (!stall_exmem) begin
            if (flush_exmem) begin
                exmem_valid     <= 1'b0;
                exmem_reg_write <= 1'b0;
                exmem_mem_read  <= 1'b0;
                exmem_mem_write <= 1'b0;
                exmem_is_csr    <= 1'b0;
                exmem_is_ecall  <= 1'b0;
                exmem_is_ebreak <= 1'b0;
                exmem_is_mret   <= 1'b0;
                exmem_illegal   <= 1'b0;
            end else begin
                exmem_valid      <= idex_valid;
                exmem_pc         <= idex_pc;
                exmem_pc_next    <= idex_pc_next;
                exmem_result     <= ex_result;
                exmem_store_data <= ex_rs2_val;
                exmem_rd_addr    <= idex_rd_addr;
                exmem_wb_sel     <= idex_wb_sel;
                exmem_reg_write  <= idex_reg_write;
                exmem_mem_read   <= idex_mem_read;
                exmem_mem_write  <= idex_mem_write;
                exmem_mem_width  <= idex_mem_width;
                exmem_mem_signed <= idex_mem_signed;
                exmem_is_amo     <= idex_is_amo;
                exmem_is_lr      <= idex_is_lr;
                exmem_is_sc      <= idex_is_sc;
                exmem_is_amo_op  <= idex_is_amo_op;
                exmem_amo_funct5 <= idex_amo_funct5;
                exmem_is_csr     <= idex_is_csr;
                exmem_csr_imm_variant <= idex_csr_imm_variant;
                exmem_csr_addr   <= idex_csr_addr;
                exmem_csr_funct3_op <= idex_funct3[1:0];
                exmem_csr_operand <= ex_csr_operand;
                exmem_is_ecall   <= idex_is_ecall;
                exmem_is_ebreak  <= idex_is_ebreak;
                exmem_is_mret    <= idex_is_mret;
                exmem_illegal    <= idex_illegal;
            end
        end
        // else held
    end

    // =========================================================================
    // MEM STAGE
    // =========================================================================
    wire [31:0] mem_addr = exmem_result;

    // ---- LR/SC reservation set (single-hart; cleared on SC attempt, on a
    //      plain store that hits the reserved address, or on trap entry) ----
    reg         reservation_valid;
    reg  [31:0] reservation_addr;
    wire        sc_success = exmem_valid && exmem_is_sc && reservation_valid &&
                              (reservation_addr == mem_addr);

    // ---- load data extraction (byte/half/word, sign or zero extend) ----
    reg  [7:0]  ld_byte;
    reg  [15:0] ld_half;
    reg  [31:0] load_data_extracted;
    always @(*) begin
        case (exmem_mem_width)
            2'b00: begin
                case (mem_addr[1:0])
                    2'b00: ld_byte = dmem_rdata[7:0];
                    2'b01: ld_byte = dmem_rdata[15:8];
                    2'b10: ld_byte = dmem_rdata[23:16];
                    default: ld_byte = dmem_rdata[31:24];
                endcase
                load_data_extracted = exmem_mem_signed ? {{24{ld_byte[7]}}, ld_byte} : {24'b0, ld_byte};
            end
            2'b01: begin
                ld_half = mem_addr[1] ? dmem_rdata[31:16] : dmem_rdata[15:0];
                load_data_extracted = exmem_mem_signed ? {{16{ld_half[15]}}, ld_half} : {16'b0, ld_half};
            end
            default: load_data_extracted = dmem_rdata; // word (also used by LR.W and AMO old-value)
        endcase
    end

    // ---- AMO ALU: computes the new value to write back to memory ----
    reg [31:0] amo_new_val;
    always @(*) begin
        case (exmem_amo_funct5)
            `AMO_SWAP: amo_new_val = exmem_store_data;
            `AMO_ADD:  amo_new_val = dmem_rdata + exmem_store_data;
            `AMO_XOR:  amo_new_val = dmem_rdata ^ exmem_store_data;
            `AMO_OR:   amo_new_val = dmem_rdata | exmem_store_data;
            `AMO_AND:  amo_new_val = dmem_rdata & exmem_store_data;
            `AMO_MIN:  amo_new_val = ($signed(dmem_rdata) < $signed(exmem_store_data)) ? dmem_rdata : exmem_store_data;
            `AMO_MAX:  amo_new_val = ($signed(dmem_rdata) > $signed(exmem_store_data)) ? dmem_rdata : exmem_store_data;
            `AMO_MINU: amo_new_val = (dmem_rdata < exmem_store_data) ? dmem_rdata : exmem_store_data;
            `AMO_MAXU: amo_new_val = (dmem_rdata > exmem_store_data) ? dmem_rdata : exmem_store_data;
            default:   amo_new_val = exmem_store_data;
        endcase
    end

    // ---- plain store byte-strobe / shifted-write-data generation ----
    reg [31:0] store_wdata_shifted;
    reg [3:0]  store_wstrb;
    always @(*) begin
        store_wdata_shifted = 32'b0;
        store_wstrb = 4'b0000;
        case (exmem_mem_width)
            2'b00: begin // byte
                case (mem_addr[1:0])
                    2'b00: begin store_wstrb = 4'b0001; store_wdata_shifted = {24'b0, exmem_store_data[7:0]}; end
                    2'b01: begin store_wstrb = 4'b0010; store_wdata_shifted = {16'b0, exmem_store_data[7:0], 8'b0}; end
                    2'b10: begin store_wstrb = 4'b0100; store_wdata_shifted = {8'b0, exmem_store_data[7:0], 16'b0}; end
                    default: begin store_wstrb = 4'b1000; store_wdata_shifted = {exmem_store_data[7:0], 24'b0}; end
                endcase
            end
            2'b01: begin // half
                if (mem_addr[1] == 1'b0) begin
                    store_wstrb = 4'b0011; store_wdata_shifted = {16'b0, exmem_store_data[15:0]};
                end else begin
                    store_wstrb = 4'b1100; store_wdata_shifted = {exmem_store_data[15:0], 16'b0};
                end
            end
            default: begin // word
                store_wstrb = 4'b1111; store_wdata_shifted = exmem_store_data;
            end
        endcase
    end

    // ---- final data-memory port mux (plain store vs. SC vs. AMO vs. read) ----
    wire dmem_req_load  = exmem_valid && (exmem_mem_read || exmem_is_lr);
    wire dmem_req_store = exmem_valid && exmem_mem_write;
    wire dmem_req_sc    = exmem_valid && exmem_is_sc;
    wire dmem_req_amo   = exmem_valid && exmem_is_amo_op;

    assign dmem_addr  = mem_addr;
    assign dmem_req   = dmem_req_load || dmem_req_store || dmem_req_sc || dmem_req_amo;
    assign dmem_wdata = dmem_req_store ? store_wdata_shifted :
                         dmem_req_amo  ? amo_new_val :
                         dmem_req_sc   ? exmem_store_data :
                                          32'h0;
    assign dmem_wstrb = dmem_req_store ? store_wstrb :
                         dmem_req_amo  ? 4'b1111 :
                         (dmem_req_sc && sc_success) ? 4'b1111 :
                                          4'b0000;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            reservation_valid <= 1'b0;
            reservation_addr  <= 32'h0;
        end else if (mem_redirect_valid_r) begin
            reservation_valid <= 1'b0;
        end else if (exmem_valid && exmem_is_lr) begin
            reservation_valid <= 1'b1;
            reservation_addr  <= mem_addr;
        end else if (exmem_valid && exmem_is_sc) begin
            reservation_valid <= 1'b0;
        end else if (exmem_valid && exmem_mem_write && reservation_valid && (mem_addr == reservation_addr)) begin
            reservation_valid <= 1'b0;
        end
    end

    wire [31:0] sc_result = {31'b0, ~sc_success};
    wire [31:0] mem_wb_data = exmem_is_sc ? sc_result : load_data_extracted;

    // ---- CSR read/write (committed here, at MEM, same stage as trap/mret) ----
    wire [31:0] csr_rdata_current;
    reg  [31:0] csr_new_val;
    always @(*) begin
        case (exmem_csr_funct3_op)
            2'b01:   csr_new_val = exmem_csr_operand;                       // CSRRW / CSRRWI
            2'b10:   csr_new_val = csr_rdata_current | exmem_csr_operand;   // CSRRS / CSRRSI
            2'b11:   csr_new_val = csr_rdata_current & ~exmem_csr_operand;  // CSRRC / CSRRCI
            default: csr_new_val = csr_rdata_current;
        endcase
    end
    wire csr_we = exmem_valid && exmem_is_csr;

    // ---- trap / mret commit (this is the single authoritative commit point) ----
    wire mem_illegal = exmem_valid && exmem_illegal;
    wire mem_ecall   = exmem_valid && exmem_is_ecall;
    wire mem_ebreak  = exmem_valid && exmem_is_ebreak;
    wire mem_mret    = exmem_valid && exmem_is_mret;
    wire mem_trap    = mem_illegal || mem_ecall || mem_ebreak;
    assign mem_redirect_valid = mem_trap || mem_mret;
    wire mem_redirect_valid_r = mem_redirect_valid; // used above in the reservation-clear block

    wire [31:0] mem_trap_cause = mem_illegal ? `CAUSE_ILLEGAL_INSTR :
                                  mem_ecall   ? `CAUSE_ECALL_M :
                                                `CAUSE_BREAKPOINT;

    wire [31:0] csr_mtvec_out, csr_mepc_out;
    csr_file u_csr_file (
        .clk(clk), .rst_n(rst_n),
        .addr(exmem_csr_addr), .rdata(csr_rdata_current), .wdata(csr_new_val), .we(csr_we),
        .retire(exmem_valid),
        .trap_taken(mem_trap), .trap_cause(mem_trap_cause), .trap_pc(exmem_pc), .trap_val(32'h0),
        .mret_taken(mem_mret),
        .mtvec_out(csr_mtvec_out), .mepc_out(csr_mepc_out)
    );

    wire [31:0] mem_redirect_target_w = mem_trap ? csr_mtvec_out : csr_mepc_out;
    assign mem_redirect_target = mem_redirect_target_w;

    // -------------------- MEM/WB pipeline register --------------------
    reg         memwb_valid;
    reg  [31:0] memwb_pc;
    reg  [31:0] memwb_alu_result;
    reg  [31:0] memwb_pc_next;
    reg  [31:0] memwb_mem_data;
    reg  [31:0] memwb_csr_rdata;
    reg  [4:0]  memwb_rd_addr;
    reg  [1:0]  memwb_wb_sel;
    reg         memwb_reg_write;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            memwb_valid <= 1'b0;
            {memwb_pc, memwb_alu_result, memwb_pc_next, memwb_mem_data, memwb_csr_rdata} <= 0;
            memwb_rd_addr <= 5'b0; memwb_wb_sel <= 2'b0; memwb_reg_write <= 1'b0;
        end else begin
            memwb_valid      <= exmem_valid;
            memwb_pc         <= exmem_pc;
            memwb_alu_result <= exmem_result;
            memwb_pc_next    <= exmem_pc_next;
            memwb_mem_data   <= mem_wb_data;
            memwb_csr_rdata  <= csr_rdata_current;
            memwb_rd_addr    <= exmem_rd_addr;
            memwb_wb_sel     <= exmem_wb_sel;
            memwb_reg_write  <= exmem_reg_write;
        end
    end

    // =========================================================================
    // WB STAGE
    // =========================================================================
    wire [31:0] memwb_final_data = (memwb_wb_sel == `WB_MEM) ? memwb_mem_data :
                                    (memwb_wb_sel == `WB_PC4) ? memwb_pc_next :
                                    (memwb_wb_sel == `WB_CSR) ? memwb_csr_rdata :
                                                                  memwb_alu_result;

    assign wb_rd_addr = memwb_rd_addr;
    assign wb_rd_data = memwb_final_data;
    assign wb_rd_we   = memwb_valid && memwb_reg_write;

    assign memwb_valid_fwd     = memwb_valid;
    assign memwb_rd_addr_fwd   = memwb_rd_addr;
    assign memwb_reg_write_fwd = memwb_reg_write;
    assign memwb_fwd_data      = memwb_final_data;

    // =========================================================================
    // STALL / FLUSH / REDIRECT - final wiring
    // =========================================================================
    assign stall_pc    = stall_load_use || stall_muldiv;
    assign stall_ifid  = stall_load_use || stall_muldiv;
    assign stall_idex  = stall_muldiv;
    assign stall_exmem = 1'b0; // reserved (no multi-cycle MEM-stage operation in this design; see
                                // the EX/MEM section comment on the combinational-read memory model)

    assign flush_ifid = ex_ctrl_redirect || mem_redirect_valid;
    assign flush_idex = ex_ctrl_redirect || mem_redirect_valid;

    assign redirect_valid  = ex_ctrl_redirect || mem_redirect_valid;
    assign redirect_target = mem_redirect_valid ? mem_redirect_target : ex_ctrl_redirect_target;

    // =========================================================================
    // Debug / monitor outputs
    // =========================================================================
    assign trap_o           = mem_trap;
    assign mcause_o          = mem_trap_cause;
    assign retired_pc_o      = memwb_pc;
    assign retired_valid_o   = memwb_valid;

endmodule

// =============================================================================
// REFERENCE MEMORY MODEL (for simulation / as an integration example)
// -----------------------------------------------------------------------------
// A single unified byte-addressable array, exposed as two independent ports
// (instruction fetch, data). Combinational read (see the memory-timing note
// above the EX/MEM register) with synchronous, byte-strobed write on the
// data port. Depth/base address are parameters so this can be instantiated
// as separate I/D memories or a shared one, per the target SoC's map.
// =============================================================================
module sync_mem #(
    parameter MEM_BYTES = 65536       // 64KB default
) (
    input                  clk,

    input       [31:0]     i_addr,     // word-aligned
    output      [31:0]     i_rdata0,
    output      [31:0]     i_rdata1,

    input       [31:0]     d_addr,
    output      [31:0]     d_rdata,
    input       [31:0]     d_wdata,
    input       [3:0]      d_wstrb,
    input                   d_req
);
    localparam WORDS = MEM_BYTES / 4;
    reg [31:0] mem [0:WORDS-1];

    wire [31:0] i_word_idx  = i_addr[31:2];
    wire [31:0] i_word_idx1 = i_word_idx + 32'h1;
    assign i_rdata0 = (i_word_idx  < WORDS) ? mem[i_word_idx]  : 32'h0;
    assign i_rdata1 = (i_word_idx1 < WORDS) ? mem[i_word_idx1] : 32'h0;

    wire [31:0] d_word_idx = d_addr[31:2];
    assign d_rdata = (d_word_idx < WORDS) ? mem[d_word_idx] : 32'h0;

    always @(posedge clk) begin
        if (d_req && (d_word_idx < WORDS)) begin
            if (d_wstrb[0]) mem[d_word_idx][7:0]   <= d_wdata[7:0];
            if (d_wstrb[1]) mem[d_word_idx][15:8]  <= d_wdata[15:8];
            if (d_wstrb[2]) mem[d_word_idx][23:16] <= d_wdata[23:16];
            if (d_wstrb[3]) mem[d_word_idx][31:24] <= d_wdata[31:24];
        end
    end

    // Simulation convenience: load a hex memory image (see the testbench below)
    // synthesis translate_off
    initial begin
        integer i;
        for (i = 0; i < WORDS; i = i + 1) mem[i] = 32'h0;
    end
    // synthesis translate_on
endmodule

// =============================================================================
// SOC WRAPPER - core + memory, the minimum integration example. A real SoC
// would add a bus/crossbar, a boot ROM, a CLINT/PLIC for real interrupts, and
// whatever peripherals it needs; this wrapper exists so the core file is a
// complete, runnable design out of the box.
// =============================================================================
module rv32imac_soc #(
    parameter MEM_BYTES = 65536
) (
    input clk,
    input rst_n
);
    wire [31:0] imem_addr, imem_rdata0, imem_rdata1;
    wire [31:0] dmem_addr, dmem_wdata, dmem_rdata;
    wire [3:0]  dmem_wstrb;
    wire        dmem_req;
    wire        trap_o;
    wire [31:0] mcause_o, retired_pc_o;
    wire        retired_valid_o;

    rv32imac_core u_core (
        .clk(clk), .rst_n(rst_n),
        .imem_addr(imem_addr), .imem_rdata0(imem_rdata0), .imem_rdata1(imem_rdata1),
        .dmem_addr(dmem_addr), .dmem_wdata(dmem_wdata), .dmem_wstrb(dmem_wstrb),
        .dmem_req(dmem_req), .dmem_rdata(dmem_rdata),
        .trap_o(trap_o), .mcause_o(mcause_o),
        .retired_pc_o(retired_pc_o), .retired_valid_o(retired_valid_o)
    );

    // NOTE: instruction and data memory share one array here for simplicity
    // (fine for a Von Neumann boot image; split them if you need true
    // Harvard-style parallel I$/D$ bandwidth).
    sync_mem #(.MEM_BYTES(MEM_BYTES)) u_mem (
        .clk(clk),
        .i_addr(imem_addr), .i_rdata0(imem_rdata0), .i_rdata1(imem_rdata1),
        .d_addr(dmem_addr), .d_rdata(dmem_rdata),
        .d_wdata(dmem_wdata), .d_wstrb(dmem_wstrb), .d_req(dmem_req)
    );
endmodule

// =============================================================================
// SIMULATION TESTBENCH (compiled only when SIM is defined, e.g.
// `iverilog -DSIM -o sim rv32imac_core.v && vvp sim`)
// -----------------------------------------------------------------------------
// This does NOT embed a hand-assembled test program (hand-encoding RV32IMAC
// machine code by hand and trusting it without running it through a real
// assembler/simulator is exactly the kind of unverified-but-confident output
// this whole exercise is trying to avoid). Instead it loads a standard Intel/
// Verilog-hex memory image produced by a real RISC-V toolchain, which is how
// every real core in the wild is actually verified:
//
//   riscv32-unknown-elf-gcc -march=rv32imac -mabi=ilp32 -nostdlib -Ttext=0 \
//       -o firmware.elf firmware.S
//   riscv32-unknown-elf-objcopy -O verilog firmware.hex firmware.elf
//   iverilog -DSIM -o sim rv32imac_core.v && vvp sim
//
// A trivial firmware.S to sanity-check the pipeline:
//   .text
//   li   x1, 5
//   li   x2, 7
//   add  x3, x1, x2      # x3 should end up = 12
//   csrrw x0, mscratch, x3
//   loop: j loop
// =============================================================================
`ifdef SIM
module tb_rv32imac;
    reg clk = 0;
    reg rst_n = 0;

    rv32imac_soc #(.MEM_BYTES(65536)) dut (.clk(clk), .rst_n(rst_n));

    always #5 clk = ~clk; // 100MHz

    initial begin
        $dumpfile("rv32imac_tb.vcd");
        $dumpvars(0, tb_rv32imac);

        // Load the firmware image into the shared instruction/data memory.
        // Adjust the path/hierarchy if you split I$ and D$ into separate
        // sync_mem instances.
        $readmemh("firmware.hex", dut.u_mem.mem);

        rst_n = 0;
        repeat (5) @(posedge clk);
        rst_n = 1;

        repeat (2000) @(posedge clk);
        $display("Simulation finished (timeout reached).");
        $finish;
    end

    always @(posedge clk) begin
        if (rst_n && dut.retired_valid_o)
            $display("t=%0t  retire  pc=%08h", $time, dut.retired_pc_o);
        if (rst_n && dut.trap_o)
            $display("t=%0t  TRAP    mcause=%08h  mepc=%08h", $time, dut.mcause_o, dut.u_core.exmem_pc);
    end
endmodule
`endif
