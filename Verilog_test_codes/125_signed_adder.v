module signed_adder #(
    parameter WIDTH = 8
) (
    input  wire signed [WIDTH-1:0] a,
    input  wire signed [WIDTH-1:0] b,
    output wire signed [WIDTH:0]   sum
);
    assign sum = a + b;
endmodule
