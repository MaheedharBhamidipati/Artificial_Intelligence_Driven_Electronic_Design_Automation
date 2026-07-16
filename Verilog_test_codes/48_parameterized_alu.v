module parameterized_alu #(
    parameter WIDTH = 8
) (
    input  wire [2:0]         opcode,
    input  wire [WIDTH-1:0]   a,
    input  wire [WIDTH-1:0]   b,
    output reg  [WIDTH-1:0]   result,
    output reg                zero_flag
);
    localparam OP_ADD = 3'b000;
    localparam OP_SUB = 3'b001;
    localparam OP_AND = 3'b010;
    localparam OP_OR  = 3'b011;
    localparam OP_XOR = 3'b100;
    localparam OP_NOT = 3'b101;

    always @(*) begin
        case (opcode)
            OP_ADD: result = a + b;
            OP_SUB: result = a - b;
            OP_AND: result = a & b;
            OP_OR:  result = a | b;
            OP_XOR: result = a ^ b;
            OP_NOT: result = ~a;
            default: result = {WIDTH{1'b0}};
        endcase
        zero_flag = (result == {WIDTH{1'b0}});
    end
endmodule
