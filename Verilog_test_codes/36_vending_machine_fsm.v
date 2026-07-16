module vending_machine_fsm (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       coin_5,
    input  wire       coin_10,
    output reg        dispense,
    output reg  [3:0] change
);
    localparam S0  = 4'd0;  // 0 cents
    localparam S5  = 4'd1;  // 5 cents
    localparam S10 = 4'd2;  // 10 cents
    localparam S15 = 4'd3;  // 15 cents
    localparam S20 = 4'd4;  // 20 cents - dispense

    reg [2:0] state, next_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S0;
        else
            state <= next_state;
    end

    always @(*) begin
        next_state = state;
        case (state)
            S0:  next_state = coin_10 ? S10 : (coin_5 ? S5  : S0);
            S5:  next_state = coin_10 ? S15 : (coin_5 ? S10 : S5);
            S10: next_state = coin_10 ? S20 : (coin_5 ? S15 : S10);
            S15: next_state = coin_10 ? S20 : (coin_5 ? S20 : S15);
            S20: next_state = S0;
            default: next_state = S0;
        endcase
    end

    always @(*) begin
        dispense = (state == S20);
        change   = 4'd0;
    end
endmodule
