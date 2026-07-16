module shift_register_8bit (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       shift_en,
    input  wire       load,
    input  wire       serial_in,
    input  wire [7:0] parallel_in,
    output reg  [7:0] data_out,
    output wire       serial_out
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data_out <= 8'd0;
        else if (load)
            data_out <= parallel_in;
        else if (shift_en)
            data_out <= {data_out[6:0], serial_in};
    end

    assign serial_out = data_out[7];
endmodule
