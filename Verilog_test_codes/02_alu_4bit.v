module alu_4bit (
    input  wire [2:0] opcode,
    input  wire [3:0] a,
    input  wire [3:0] b,
    output reg  [4:0] result,
    output reg        zero_flag
);
    localparam OP_ADD  = 3'b000;
    localparam OP_SUB  = 3'b001;
    localparam OP_AND  = 3'b010;
    localparam OP_OR   = 3'b011;
    localparam OP_XOR  = 3'b100;
    localparam OP_NAND = 3'b101;
    localparam OP_NOR  = 3'b110;
    localparam OP_XNOR = 3'b111;

    always @(*) begin
        case (opcode)
            OP_ADD:  result = {1'b0, a} + {1'b0, b};
            OP_SUB:  result = {1'b0, a} - {1'b0, b};
            OP_AND:  result = {1'b0, a & b};
            OP_OR:   result = {1'b0, a | b};
            OP_XOR:  result = {1'b0, a ^ b};
            OP_NAND: result = {1'b0, ~(a & b)};
            OP_NOR:  result = {1'b0, ~(a | b)};
            OP_XNOR: result = {1'b0, ~(a ^ b)};
            default: result = 5'b00000;
        endcase
        zero_flag = (result == 5'b00000);
    end
endmodule
