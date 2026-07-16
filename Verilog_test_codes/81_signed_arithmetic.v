module signed_arithmetic #(
    parameter WIDTH = 8
) (
    input  wire signed [WIDTH-1:0]   a,
    input  wire signed [WIDTH-1:0]   b,
    output wire signed [WIDTH:0]     sum,
    output wire signed [WIDTH:0]     diff,
    output wire signed [2*WIDTH-1:0] product,
    output wire                      a_is_negative
);
    assign sum           = a + b;
    assign diff          = a - b;
    assign product        = a * b;
    assign a_is_negative = a[WIDTH-1];
endmodule
