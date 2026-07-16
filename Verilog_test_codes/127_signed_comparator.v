module signed_comparator #(
    parameter WIDTH = 8
) (
    input  wire signed [WIDTH-1:0] a,
    input  wire signed [WIDTH-1:0] b,
    output wire                    eq,
    output wire                    gt,
    output wire                    lt
);
    assign eq = (a == b);
    assign gt = (a > b);
    assign lt = (a < b);
endmodule
