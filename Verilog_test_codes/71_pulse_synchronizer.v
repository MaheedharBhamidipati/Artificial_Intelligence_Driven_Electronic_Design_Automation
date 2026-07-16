module pulse_synchronizer (
    input  wire src_clk,
    input  wire src_rst_n,
    input  wire pulse_in,
    input  wire dst_clk,
    input  wire dst_rst_n,
    output wire pulse_out
);
    reg toggle_ff;
    reg meta1, meta2, meta3;

    always @(posedge src_clk or negedge src_rst_n) begin
        if (!src_rst_n)
            toggle_ff <= 1'b0;
        else if (pulse_in)
            toggle_ff <= ~toggle_ff;
    end

    always @(posedge dst_clk or negedge dst_rst_n) begin
        if (!dst_rst_n) begin
            meta1 <= 1'b0;
            meta2 <= 1'b0;
            meta3 <= 1'b0;
        end else begin
            meta1 <= toggle_ff;
            meta2 <= meta1;
            meta3 <= meta2;
        end
    end

    assign pulse_out = meta2 ^ meta3;
endmodule
