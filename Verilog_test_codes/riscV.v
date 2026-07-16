

`timescale 1ns/1ps

module RISC5_top(input clk, input rst);

  wire [31:0] PC, PC_plus4, PC_branch, PC_jalr_target, PC_jal_target, PC_next;
  wire [31:0] Instr;

  wire [6:0] opcode = Instr[6:0];
  wire [2:0] funct3 = Instr[14:12];
  wire [6:0] funct7 = Instr[31:25];
  wire [4:0] rs1 = Instr[19:15], rs2 = Instr[24:20], rd = Instr[11:7];

  wire Branch, MemRead, MemtoReg, MemWrite, ALUSrc, RegWrite;
  wire Jal, Jalr, Lui, Auipc;
  wire [1:0] ALUOp;
  wire [3:0] ALUControl;
  wire Zero;

  wire [31:0] RD1, RD2, Imm;
  wire [31:0] ALU_in2, ALU_out, ReadData, WriteData;

  pcAdder PCA(PC, PC_plus4);

  assign PC_branch = PC + Imm;
  assign PC_jal_target = PC + Imm;
  assign PC_jalr_target = (RD1 + Imm) & 32'hfffffffe;

  wire slt_result = ALU_out[0]; 

  wire takeBranch = (Branch && (
                      (funct3 == 3'b000 &&  Zero) ||     // BEQ
                      (funct3 == 3'b001 && !Zero) ||     // BNE
                      (funct3 == 3'b100 &&  slt_result) || // BLT
                      (funct3 == 3'b101 && !slt_result) || // BGE
                      (funct3 == 3'b110 &&  slt_result) || // BLTU (using ALU[0] for comparison result)
                      (funct3 == 3'b111 && !slt_result)    // BGEU
                    ));

  assign PC_next = Jalr        ? PC_jalr_target :
                   Jal         ? PC_jal_target  :
                   takeBranch  ? PC_branch      :
                                 PC_plus4;

  programCounter PC_reg(clk, rst, PC_next, PC);
  instructionMemory IM(PC, Instr);


  controlUnit CU(opcode, Branch, MemRead, MemtoReg, ALUOp, MemWrite, ALUSrc, RegWrite, Jal, Jalr, Lui, Auipc);
  
  registerFile RF(clk, RegWrite, rs1, rs2, rd, WriteData, RD1, RD2);
  signExtend SE(Instr, opcode, Imm); 

  mux2to1 MUX_ALU(RD2, Imm, ALUSrc, ALU_in2);
  aluControl ALUCTRL(ALUOp, funct3, funct7, ALUControl);
  alu ALU(RD1, ALU_in2, ALUControl, ALU_out, Zero);
  dataMemory DM(clk, MemWrite, MemRead, ALU_out, RD2, ReadData);


  wire [31:0] WriteData_from_mem;
  wire [31:0] WriteData_from_jal = PC_plus4;
  wire [31:0] WriteData_from_lui = Imm;
  wire [31:0] WriteData_from_auipc = PC + Imm;

  wire write_jal = Jal | Jalr;
  wire write_lui = Lui;
  wire write_auipc = Auipc;


  mux2to1 MUX_MEM(ALU_out, ReadData, MemtoReg, WriteData_from_mem);

  assign WriteData = write_lui   ? WriteData_from_lui   :
                   write_auipc ? WriteData_from_auipc :
                   write_jal   ? WriteData_from_jal   :
                   MemtoReg    ? ReadData             :
                                  ALU_out;
  initial begin
    $monitor("T=%0t | PC=%h Instr=%h | Opcode = %b | funct3 = %b | funct7 = %b | Imm=%h | WriteData=%h", $time, PC, Instr, opcode, funct3, funct7, Imm, WriteData);
  end
endmodule

// =============================================================================================================

`timescale 1ns/1ps
module programCounter(
  input clk, rst,
  input [31:0] pc_in,
  output reg [31:0] pc_out
);
  always @(posedge clk or posedge rst) begin
    if (rst)
      pc_out <= 0;
    else
      pc_out <= pc_in;
//     $display("PC updated to 0x%08h at time %0t", rst ? 0 : pc_in, $time);
  end
endmodule

// =========================================================================================================================

`timescale 1ns/1ps
module instructionMemory(
  input [31:0] addr,
  output [31:0] instruction
);

  reg [31:0] memory [0:255];
  integer i;

  assign instruction = memory[addr[9:2]];

  initial begin
    for (i = 0; i < 256; i = i + 1)
      memory[i] = 32'h00000013; 
    $readmemh("test_program.hex", memory);
// 	$display("Loaded instruction memory from test_program.hex");
  end
endmodule

// ==================================================================================================

`timescale 1ns / 1ps
module controlUnit (
    input [6:0] opcode,
    output reg Branch,
    MemRead,
    MemtoReg,
    output reg [1:0] ALUOp,
    output reg MemWrite,
    ALUSrc,
    RegWrite,
    output reg Jal,
    Jalr,
    output reg Lui,
    Auipc
);

  always @(*) begin
    // Default values
    Branch = 0;
    MemRead = 0;
    MemtoReg = 0;
    MemWrite = 0;
    ALUSrc = 0;
    RegWrite = 0;
    ALUOp = 2'b00;
    Jal = 0;
    Jalr = 0;
    Lui = 0;
    Auipc = 0;

    case (opcode)
      7'b0110011: begin  // R-type
        ALUSrc = 0;
        RegWrite = 1;
        ALUOp = 2'b10;
      end

      7'b0010011: begin  // I-type ALU (ADDI, SLTI, ANDI, SLLI, etc.)
        ALUSrc = 1;
        RegWrite = 1;
        ALUOp = 2'b11;
      end

      7'b0000011: begin  // Load (LB, LH, LW, LBU, LHU)
        ALUSrc   = 1;
        RegWrite = 1;
        MemRead  = 1;
        MemtoReg = 1;
      end

      7'b0100011: begin  // Store (SB, SH, SW)
        ALUSrc   = 1;
        MemWrite = 1;
      end

      7'b1100011: begin  // Branch (BEQ, BNE, etc.)
        ALUSrc = 0;
        Branch = 1;
        ALUOp  = 2'b01;
      end

      7'b1101111: begin  // JAL
        RegWrite = 1;
        Jal = 1;
      end

      7'b1100111: begin  // JALR
        RegWrite = 1;
        Jalr = 1;
        ALUSrc = 1;
      end

      7'b0110111: begin  // LUI
        RegWrite = 1;
        Lui = 1;
      end

      7'b0010111: begin  // AUIPC
        RegWrite = 1;
        Auipc = 1;
      end

      default: begin
        // Already covered by default values above
      end
    endcase
  end

endmodule

// ==================================================================================================================

`timescale 1ns/1ps
module registerFile(
  input clk,
  input RegWrite,
  input [4:0] rs1, rs2, rd,
  input [31:0] writeData,
  output [31:0] readData1, readData2
);

  reg [31:0] registers[0:31];
  integer i;
  assign readData1 = (rs1 != 5'd0) ? registers[rs1] : 32'b0;
  assign readData2 = (rs2 != 5'd0) ? registers[rs2] : 32'b0;
  always @(posedge clk) begin
    if (RegWrite && rd != 5'd0) begin
      registers[rd] <= writeData;
      //$display("RegWrite: x%0d <= %0d at time %0t", rd, writeData, $time);
    end
  end
  initial begin
    for (i = 0; i < 32; i = i + 1) begin
      registers[i] = 32'b0;
    end
  end
endmodule

// =======================================================================================================

`timescale 1ns/1ps
module alu(
  input [31:0] A, B,
  input [3:0] ALUControl,
  output reg [31:0] Result,
  output reg Zero
);
  always @(*) begin
    case (ALUControl)
      4'b0000: Result = A & B;
      4'b0001: Result = A | B;
      4'b0010: Result = A + B;
      4'b0110: Result = A - B;
      4'b0111: Result = ($signed(A) < $signed(B)) ? 32'b1 : 32'b0;
      4'b1000: Result = (A < B) ? 32'd1 : 32'd0;
      4'b0011: Result = A ^ B;
      4'b0100: Result = A << B[4:0];
      4'b0101: Result = A >> B[4:0];
      4'b1101: Result = $signed(A) >>> B[4:0];
      default: Result = 32'h00000000;
    endcase

    Zero = (Result == 32'b0);  
    //$display("ALU: A=%0d, B=%0d, ctrl=%b, out=%0d", A, B, ALUControl, Result);
  end
endmodule

// =================================================================================================================

`timescale 1ns / 1ps
module aluControl (
    input [1:0] ALUOp,
    input [2:0] funct3,
    input [6:0] funct7,
    output reg [3:0] ALUControl
);
  always @(*) begin
    case (ALUOp)
      2'b00:  // Load/Store
      ALUControl = 4'b0010;  // ADD

      2'b01: begin  // Branch instructions
        case (funct3)
          3'b000:  ALUControl = 4'b0110;  // BEQ → SUB
          3'b001:  ALUControl = 4'b0110;  // BNE → SUB
          3'b100:  ALUControl = 4'b0111;  // BLT → SLT
          3'b101:  ALUControl = 4'b0111;  // BGE → SLT
          3'b110:  ALUControl = 4'b1000;  // BLTU → SLTU
          3'b111:  ALUControl = 4'b1000;  // BGEU → SLTU
          default: ALUControl = 4'b1111;
        endcase
      end

      2'b10, 2'b11: begin
        case (funct3)
          3'b000: begin
            if (funct7 == 7'b0100000 && ALUOp == 2'b10) ALUControl = 4'b0110;  // SUB (R-type)
            else ALUControl = 4'b0010;  // ADD / ADDI
          end
          3'b001:  ALUControl = 4'b0100;  // SLL / SLLI
          3'b010:  ALUControl = 4'b0111;  // SLT / SLTI
          3'b011:  ALUControl = 4'b1000;  // SLTU / SLTIU
          3'b100:  ALUControl = 4'b0011;  // XOR / XORI
          3'b101: begin
            if (funct7 == 7'b0000000) ALUControl = 4'b0101;  // SRL / SRLI
            else if (funct7 == 7'b0100000) ALUControl = 4'b1101;  // SRA / SRAI
            else ALUControl = 4'b1111;  // Undefined
          end
          3'b110:  ALUControl = 4'b0001;  // OR / ORI
          3'b111:  ALUControl = 4'b0000;  // AND / ANDI
          default: ALUControl = 4'b1111;
        endcase
      end

      default: ALUControl = 4'b1111;
    endcase
  end
endmodule

// ========================================================================================================

`timescale 1ns/1ps
module signExtend(
  input [31:0] instr,
  input [6:0] opcode,
  output reg [31:0] imm
);

always @(*) begin
  case (opcode)
    7'b0000011, // I-type: lw
    7'b0010011, // I-type: addi, andi, ori, etc.
    7'b1100111: // I-type: jalr
      imm = {{20{instr[31]}}, instr[31:20]};

    7'b0100011: // S-type: sw
      imm = {{20{instr[31]}}, instr[31:25], instr[11:7]};

    7'b1100011: // B-type: beq, bne, blt, etc.
      imm = {{19{instr[31]}}, instr[31], instr[7], instr[30:25], instr[11:8], 1'b0};

    7'b1101111: // J-type: jal
      imm = {{11{instr[31]}}, instr[31], instr[19:12], instr[20], instr[30:21], 1'b0};

    7'b0110111, // U-type: lui
    7'b0010111: // U-type: auipc
      imm = {instr[31:12], 12'b0};

    default:
      imm = 32'd0;
  endcase
end
endmodule

// =========================================================================================

`timescale 1ns/1ps
module dataMemory(
  input clk,
  input MemWrite, MemRead,
  input [31:0] addr, writeData,
  output [31:0] readData
);
  reg [31:0] memory [0:255]; 
  wire [7:0] mem_index = addr[9:2]; 
  integer i;
  always @(posedge clk) begin
    if (MemWrite) begin
      if (mem_index < 256) begin
        memory[mem_index] <= writeData;
      end else begin
        $display("Write out-of-bounds: addr=0x%0h", addr);
      end
    end
  end
  assign readData = (MemRead && mem_index < 256) ? memory[mem_index] : 32'b0;
  initial begin
    for (i = 0; i < 256; i = i + 1) begin
      memory[i] = 32'd0;
    end
  end
endmodule

// =======================================================================

`timescale 1ns/1ps
module mux2to1(
  input [31:0] a, b,
  input sel,
  output [31:0] out
);
  assign out = sel ? b : a;
endmodule

// ========================================================================

`timescale 1ns/1ps
module pcAdder(
  input [31:0] pc,
  output [31:0] pc_next
);
  assign pc_next = pc + 4;
endmodule

