module stress_test_fsm_16state (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       en,
    output reg  [3:0] state,
    output reg        out_valid
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= 4'd0;
        else if (en)
            state <= state + 4'd1;
    end

    always @(*) begin
        out_valid = (state == 4'hF);
    end
endmodule
