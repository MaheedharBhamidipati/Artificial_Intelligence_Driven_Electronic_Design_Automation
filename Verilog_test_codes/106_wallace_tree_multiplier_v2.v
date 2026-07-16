module wallace_tree_multiplier_v2 #(
    parameter WIDTH = 8
) (
    input  wire [WIDTH-1:0]   a,
    input  wire [WIDTH-1:0]   b,
    output wire [2*WIDTH-1:0] product
);
    // Partial products generated explicitly; synthesis tools reduce
    // this addition tree using Wallace-tree-style carry-save adders.
    wire [WIDTH-1:0] pp [0:WIDTH-1];
    genvar i;
    generate
        for (i = 0; i < WIDTH; i = i + 1) begin : pp_gen
            assign pp[i] = a & {WIDTH{b[i]}};
        end
    endgenerate

    integer k;
    reg [2*WIDTH-1:0] acc_sum;
    always @(*) begin
        acc_sum = {2*WIDTH{1'b0}};
        for (k = 0; k < WIDTH; k = k + 1) begin
            acc_sum = acc_sum + (pp[k] << k);
        end
    end

    assign product = acc_sum;
endmodule
