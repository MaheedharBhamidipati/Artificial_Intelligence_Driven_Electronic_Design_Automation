module mux_256to1 #(
    parameter WIDTH = 1
) (
    input  wire [255:0][WIDTH-1:0] data_in,
    input  wire [7:0]              sel,
    output wire [WIDTH-1:0]        data_out
);
    assign data_out = data_in[sel];
endmodule
