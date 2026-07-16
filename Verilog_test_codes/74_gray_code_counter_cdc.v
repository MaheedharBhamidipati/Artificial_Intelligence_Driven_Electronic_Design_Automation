module gray_code_counter_cdc #(
    parameter WIDTH = 4
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             en,
    output reg  [WIDTH-1:0] gray_count,
    output reg  [WIDTH-1:0] bin_count
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bin_count  <= {WIDTH{1'b0}};
            gray_count <= {WIDTH{1'b0}};
        end else if (en) begin
            bin_count  <= bin_count + 1'b1;
            gray_count <= (bin_count + 1'b1) ^ ((bin_count + 1'b1) >> 1);
        end
    end
endmodule
