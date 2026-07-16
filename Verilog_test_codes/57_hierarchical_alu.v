module arithmetic_unit #(
    parameter WIDTH = 8
) (
    input  wire             sub,
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output wire [WIDTH-1:0] result
);
    assign result = sub ? (a - b) : (a + b);
endmodule

module logic_unit #(
    parameter WIDTH = 8
) (
    input  wire [1:0]       op,
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output reg  [WIDTH-1:0] result
);
    always @(*) begin
        case (op)
            2'b00: result = a & b;
            2'b01: result = a | b;
            2'b10: result = a ^ b;
            2'b11: result = ~a;
            default: result = {WIDTH{1'b0}};
        endcase
    end
endmodule

module hierarchical_alu #(
    parameter WIDTH = 8
) (
    input  wire             use_logic,
    input  wire             sub,
    input  wire [1:0]       logic_op,
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output wire [WIDTH-1:0] result
);
    wire [WIDTH-1:0] arith_result;
    wire [WIDTH-1:0] logic_result;

    arithmetic_unit #(.WIDTH(WIDTH)) u_arith (
        .sub(sub), .a(a), .b(b), .result(arith_result)
    );

    logic_unit #(.WIDTH(WIDTH)) u_logic (
        .op(logic_op), .a(a), .b(b), .result(logic_result)
    );

    assign result = use_logic ? logic_result : arith_result;
endmodule
