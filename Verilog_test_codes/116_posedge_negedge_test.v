module posedge_negedge_test (
    input  wire clk,
    input  wire rst_n,
    input  wire d,
    output reg  q_pos,
    output reg  q_neg
);
    // Positive-edge triggered register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            q_pos <= 1'b0;
        else
            q_pos <= d;
    end

    // Negative-edge triggered register
    always @(negedge clk or negedge rst_n) begin
        if (!rst_n)
            q_neg <= 1'b0;
        else
            q_neg <= d;
    end
endmodule
