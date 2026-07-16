module toggle_synchronizer (
    input  wire src_clk,
    input  wire src_rst_n,
    input  wire event_in,
    input  wire dst_clk,
    input  wire dst_rst_n,
    output reg  event_out
);
    reg toggle_reg;
    reg sync1, sync2, sync3;

    always @(posedge src_clk or negedge src_rst_n) begin
        if (!src_rst_n)
            toggle_reg <= 1'b0;
        else if (event_in)
            toggle_reg <= ~toggle_reg;
    end

    always @(posedge dst_clk or negedge dst_rst_n) begin
        if (!dst_rst_n) begin
            sync1 <= 1'b0;
            sync2 <= 1'b0;
            sync3 <= 1'b0;
        end else begin
            sync1 <= toggle_reg;
            sync2 <= sync1;
            sync3 <= sync2;
        end
    end

    always @(*) begin
        event_out = sync2 ^ sync3;
    end
endmodule
