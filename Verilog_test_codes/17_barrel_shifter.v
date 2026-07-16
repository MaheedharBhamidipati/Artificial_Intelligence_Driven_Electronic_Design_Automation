module barrel_shifter (
    input  wire [7:0] data_in,
    input  wire [2:0] shift_amt,
    input  wire [1:0] mode, // 00: logical left, 01: logical right, 10: rotate left, 11: rotate right
    output reg  [7:0] data_out
);
    always @(*) begin
        case (mode)
            2'b00: data_out = data_in << shift_amt;
            2'b01: data_out = data_in >> shift_amt;
            2'b10: data_out = (data_in << shift_amt) | (data_in >> (8 - shift_amt));
            2'b11: data_out = (data_in >> shift_amt) | (data_in << (8 - shift_amt));
            default: data_out = data_in;
        endcase
    end
endmodule
