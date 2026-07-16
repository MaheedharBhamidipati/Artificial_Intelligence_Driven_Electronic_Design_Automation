module part_select_test (
    input  wire [15:0] data_in,
    output wire [7:0]  upper_byte,
    output wire [7:0]  lower_byte,
    output wire [3:0]  nibble_1
);
    assign upper_byte = data_in[15:8];
    assign lower_byte = data_in[7:0];
    assign nibble_1   = data_in[7:4];
endmodule
