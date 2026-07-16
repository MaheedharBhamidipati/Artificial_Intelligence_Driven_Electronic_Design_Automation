module barrel_shifter_v2 #(
    parameter WIDTH = 8
) (
    input  wire [WIDTH-1:0]         data_in,
    input  wire [$clog2(WIDTH)-1:0] shift_amt,
    input  wire [1:0]               mode, // 00: logical left, 01: logical right, 10: arithmetic right, 11: rotate
    input  wire                     rotate_left, // used only when mode == 2'b11
    output reg  [WIDTH-1:0]         data_out
);
    always @(*) begin
        case (mode)
            2'b00: data_out = data_in << shift_amt;
            2'b01: data_out = data_in >> shift_amt;
            2'b10: data_out = $signed(data_in) >>> shift_amt;
            2'b11: data_out = rotate_left ?
                              ((data_in << shift_amt) | (data_in >> (WIDTH - shift_amt))) :
                              ((data_in >> shift_amt) | (data_in << (WIDTH - shift_amt)));
            default: data_out = data_in;
        endcase
    end
endmodule
