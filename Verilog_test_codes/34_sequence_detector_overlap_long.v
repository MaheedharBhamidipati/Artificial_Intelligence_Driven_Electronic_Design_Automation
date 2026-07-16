// Detects overlapping pattern 1101110110100101 (16 bits) using a shift-register compare
module sequence_detector_overlap_long (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        din,
    output wire         detected
);
    localparam [15:0] PATTERN = 16'b1101110110100101;

    reg [15:0] shift_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            shift_reg <= 16'd0;
        else
            shift_reg <= {shift_reg[14:0], din};
    end

    assign detected = (shift_reg == PATTERN);
endmodule
