module two_ff_synchronizer (
    input  wire dst_clk,
    input  wire rst_n,
    input  wire async_in,
    output reg  sync_out
);
    reg meta;

    always @(posedge dst_clk or negedge rst_n) begin
        if (!rst_n) begin
            meta     <= 1'b0;
            sync_out <= 1'b0;
        end else begin
            meta     <= async_in;
            sync_out <= meta;
        end
    end
endmodule
