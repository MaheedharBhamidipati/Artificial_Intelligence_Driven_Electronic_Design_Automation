module wallace_tree_multiplier #(
    parameter WIDTH = 8
) (
    input  wire [WIDTH-1:0]   a,
    input  wire [WIDTH-1:0]   b,
    output wire [2*WIDTH-1:0] product
);
    // Behavioral RTL for synthesis; synthesis tools map multiplication
    // to Wallace-tree-based multiplier structures automatically.
    assign product = a * b;
endmodule
