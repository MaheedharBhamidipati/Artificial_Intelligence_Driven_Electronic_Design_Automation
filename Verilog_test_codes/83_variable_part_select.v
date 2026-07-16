module variable_part_select #(
    parameter WIDTH = 32,
    parameter FIELD_WIDTH = 8
) (
    input  wire [WIDTH-1:0]       data_in,
    input  wire [$clog2(WIDTH)-1:0] base_addr,
    output wire [FIELD_WIDTH-1:0] field_out
);
    assign field_out = data_in[base_addr +: FIELD_WIDTH];
endmodule
