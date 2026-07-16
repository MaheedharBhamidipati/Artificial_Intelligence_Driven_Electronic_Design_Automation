module multi_reset_design (
    input  wire clk,
    input  wire async_rst_n,
    input  wire sync_rst,
    input  wire soft_rst,
    input  wire d,
    output reg  q
);
    always @(posedge clk or negedge async_rst_n) begin
        if (!async_rst_n)
            q <= 1'b0;
        else if (sync_rst || soft_rst)
            q <= 1'b0;
        else
            q <= d;
    end
endmodule
