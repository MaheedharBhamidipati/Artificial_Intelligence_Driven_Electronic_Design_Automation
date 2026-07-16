module array_multiplier_v2 #(
    parameter WIDTH = 8
) (
    input  wire [WIDTH-1:0]   a,
    input  wire [WIDTH-1:0]   b,
    output wire [2*WIDTH-1:0] product
);
    // Classical array-multiplier structure: sum of shifted partial products
    wire [WIDTH-1:0] partial_product [0:WIDTH-1];
    genvar i;
    generate
        for (i = 0; i < WIDTH; i = i + 1) begin : pp_gen
            assign partial_product[i] = a & {WIDTH{b[i]}};
        end
    endgenerate

    integer j;
    reg [2*WIDTH-1:0] sum;
    always @(*) begin
        sum = {2*WIDTH{1'b0}};
        for (j = 0; j < WIDTH; j = j + 1) begin
            sum = sum + (partial_product[j] << j);
        end
    end

    assign product = sum;
endmodule
