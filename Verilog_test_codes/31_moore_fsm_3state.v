module moore_fsm_3state (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       in,
    output reg        out
);
    localparam S0 = 2'd0, S1 = 2'd1, S2 = 2'd2;
    reg [1:0] state, next_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S0;
        else
            state <= next_state;
    end

    always @(*) begin
        case (state)
            S0: next_state = in ? S1 : S0;
            S1: next_state = in ? S2 : S0;
            S2: next_state = in ? S2 : S0;
            default: next_state = S0;
        endcase
    end

    always @(*) begin
        case (state)
            S0: out = 1'b0;
            S1: out = 1'b0;
            S2: out = 1'b1;
            default: out = 1'b0;
        endcase
    end
endmodule
