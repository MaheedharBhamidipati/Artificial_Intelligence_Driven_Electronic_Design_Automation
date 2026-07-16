module signed_subtractor #(
    parameter WIDTH = 8
) (
    input  wire signed [WIDTH-1:0] a,
    input  wire signed [WIDTH-1:0] b,
    output wire signed [WIDTH:0]   diff
);
    assign diff = a - b;
endmodule
