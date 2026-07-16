module sign_extension #(
    parameter IN_WIDTH  = 8,
    parameter OUT_WIDTH = 16
) (
    input  wire signed [IN_WIDTH-1:0]  data_in,
    output wire signed [OUT_WIDTH-1:0] data_out
);
    assign data_out = {{(OUT_WIDTH-IN_WIDTH){data_in[IN_WIDTH-1]}}, data_in};
endmodule
