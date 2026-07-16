module demux_1to16 #(
    parameter WIDTH = 1
) (
    input  wire [WIDTH-1:0]        data_in,
    input  wire [3:0]              sel,
    output wire [15:0][WIDTH-1:0]  data_out
);
    genvar i;
    generate
        for (i = 0; i < 16; i = i + 1) begin : demux_gen
            assign data_out[i] = (sel == i[3:0]) ? data_in : {WIDTH{1'b0}};
        end
    endgenerate
endmodule
