module crossbar_16x16 #(
    parameter WIDTH = 8
) (
    input  wire [15:0][WIDTH-1:0]  data_in,
    input  wire [15:0][3:0]        sel,
    output wire [15:0][WIDTH-1:0]  data_out
);
    genvar i;
    generate
        for (i = 0; i < 16; i = i + 1) begin : xbar_gen
            assign data_out[i] = data_in[sel[i]];
        end
    endgenerate
endmodule
