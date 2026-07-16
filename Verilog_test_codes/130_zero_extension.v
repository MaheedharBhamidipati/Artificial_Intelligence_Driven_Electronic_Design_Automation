module zero_extension #(
    parameter IN_WIDTH  = 8,
    parameter OUT_WIDTH = 16
) (
    input  wire [IN_WIDTH-1:0]  data_in,
    output wire [OUT_WIDTH-1:0] data_out
);
    assign data_out = {{(OUT_WIDTH-IN_WIDTH){1'b0}}, data_in};
endmodule
