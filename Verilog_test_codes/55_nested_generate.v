module nested_generate #(
    parameter ROWS = 4,
    parameter COLS = 4,
    parameter WIDTH = 8
) (
    input  wire [ROWS-1:0][COLS-1:0][WIDTH-1:0] matrix_in,
    output wire [ROWS-1:0][COLS-1:0][WIDTH-1:0] matrix_out
);
    genvar r, c;
    generate
        for (r = 0; r < ROWS; r = r + 1) begin : row_gen
            for (c = 0; c < COLS; c = c + 1) begin : col_gen
                assign matrix_out[r][c] = matrix_in[r][c] + 1'b1;
            end
        end
    endgenerate
endmodule
