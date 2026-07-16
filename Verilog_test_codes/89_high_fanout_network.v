module high_fanout_network #(
    parameter FANOUT = 64
) (
    input  wire                clk,
    input  wire                rst_n,
    input  wire                source_signal,
    output wire [FANOUT-1:0]    fanout_out
);
    reg buffered_signal;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            buffered_signal <= 1'b0;
        else
            buffered_signal <= source_signal;
    end

    genvar i;
    generate
        for (i = 0; i < FANOUT; i = i + 1) begin : fanout_gen
            assign fanout_out[i] = buffered_signal;
        end
    endgenerate
endmodule
