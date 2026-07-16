module alu_8bit (
    input  wire [3:0] opcode,
    input  wire [7:0] a,
    input  wire [7:0] b,
    output reg  [8:0] result,
    output reg        zero_flag,
    output reg        carry_flag,
    output reg        eq_flag,
    output reg        gt_flag,
    output reg        lt_flag
);
    localparam OP_ADD = 4'h0;
    localparam OP_SUB = 4'h1;
    localparam OP_AND = 4'h2;
    localparam OP_OR  = 4'h3;
    localparam OP_XOR = 4'h4;
    localparam OP_NOT = 4'h5;
    localparam OP_SLL = 4'h6;
    localparam OP_SRL = 4'h7;
    localparam OP_CMP = 4'h8;

    always @(*) begin
        result     = 9'b0;
        carry_flag = 1'b0;
        case (opcode)
            OP_ADD: result = {1'b0, a} + {1'b0, b};
            OP_SUB: result = {1'b0, a} - {1'b0, b};
            OP_AND: result = {1'b0, a & b};
            OP_OR:  result = {1'b0, a | b};
            OP_XOR: result = {1'b0, a ^ b};
            OP_NOT: result = {1'b0, ~a};
            OP_SLL: result = {1'b0, a} << b[2:0];
            OP_SRL: result = {1'b0, a} >> b[2:0];
            OP_CMP: result = {1'b0, a} - {1'b0, b};
            default: result = 9'b0;
        endcase
        carry_flag = result[8];
        zero_flag  = (result[7:0] == 8'b0);
        eq_flag    = (a == b);
        gt_flag    = (a > b);
        lt_flag    = (a < b);
    end
endmodule
