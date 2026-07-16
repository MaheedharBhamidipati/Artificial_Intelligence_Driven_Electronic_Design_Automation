module alu_2bit (
    input  wire [2:0] opcode,
    input  wire [1:0] a,
    input  wire [1:0] b,
    output reg  [2:0] result,
    output reg        zero_flag
);
    localparam OP_ADD = 3'b000;
    localparam OP_SUB = 3'b001;
    localparam OP_AND = 3'b010;
    localparam OP_OR  = 3'b011;
    localparam OP_XOR = 3'b100;
    localparam OP_NOT = 3'b101;

    always @(*) begin
        case (opcode)
            OP_ADD: result = {1'b0, a} + {1'b0, b};
            OP_SUB: result = {1'b0, a} - {1'b0, b};
            OP_AND: result = {1'b0, a & b};
            OP_OR:  result = {1'b0, a | b};
            OP_XOR: result = {1'b0, a ^ b};
            OP_NOT: result = {1'b0, ~a};
            default: result = 3'b000;
        endcase
        zero_flag = (result == 3'b000);
    end
endmodule
