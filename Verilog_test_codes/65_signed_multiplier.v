module signed_multiplier #(
    parameter WIDTH = 8
) (
    input  wire signed [WIDTH-1:0]   a,
    input  wire signed [WIDTH-1:0]   b,
    output wire signed [2*WIDTH-1:0] product
);
    assign product = a * b;
endmodule
