module universal_shift_register (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [1:0] mode, // 00: hold, 01: shift right, 10: shift left, 11: parallel load
    input  wire       serial_in_left,
    input  wire       serial_in_right,
    input  wire [7:0] parallel_in,
    output reg  [7:0] data_out
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data_out <= 8'd0;
        else begin
            case (mode)
                2'b00: data_out <= data_out;
                2'b01: data_out <= {serial_in_right, data_out[7:1]};
                2'b10: data_out <= {data_out[6:0], serial_in_left};
                2'b11: data_out <= parallel_in;
                default: data_out <= data_out;
            endcase
        end
    end
endmodule
