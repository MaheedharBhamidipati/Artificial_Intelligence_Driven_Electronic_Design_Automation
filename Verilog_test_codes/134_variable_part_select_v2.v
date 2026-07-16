module variable_part_select_v2 #(
    parameter WIDTH       = 32,
    parameter FIELD_WIDTH = 8
) (
    input  wire [WIDTH-1:0]           data_in,
    input  wire [$clog2(WIDTH)-1:0]   base_idx_up,
    input  wire [$clog2(WIDTH)-1:0]   base_idx_down,
    output wire [FIELD_WIDTH-1:0]     field_up,
    output wire [FIELD_WIDTH-1:0]     field_down
);
    // +: selects an increasing range starting at base_idx_up
    assign field_up   = data_in[base_idx_up +: FIELD_WIDTH];
    // -: selects a decreasing range ending at base_idx_down
    assign field_down = data_in[base_idx_down -: FIELD_WIDTH];
endmodule
