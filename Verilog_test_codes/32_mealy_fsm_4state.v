module mealy_fsm_4state (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       in,
    output reg        out
);
    localparam S0 = 2'd0, S1 = 2'd1, S2 = 2'd2, S3 = 2'd3;
    reg [1:0] state, next_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S0;
        else
            state <= next_state;
    end

    always @(*) begin
        next_state = state;
        out        = 1'b0;
        case (state)
            S0: begin
                next_state = in ? S1 : S0;
                out = 1'b0;
            end
            S1: begin
                next_state = in ? S2 : S0;
                out = in ? 1'b0 : 1'b1;
            end
            S2: begin
                next_state = in ? S3 : S0;
                out = in ? 1'b0 : 1'b1;
            end
            S3: begin
                next_state = in ? S3 : S0;
                out = 1'b1;
            end
            default: begin
                next_state = S0;
                out = 1'b0;
            end
        endcase
    end
endmodule
