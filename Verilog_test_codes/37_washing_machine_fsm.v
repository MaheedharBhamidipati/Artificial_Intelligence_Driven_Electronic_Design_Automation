module washing_machine_fsm (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       start,
    input  wire       cycle_done,
    output reg  [2:0] state_out,
    output reg        wash_on,
    output reg        rinse_on,
    output reg        spin_on
);
    localparam IDLE  = 3'd0;
    localparam WASH  = 3'd1;
    localparam RINSE = 3'd2;
    localparam SPIN  = 3'd3;
    localparam DONE  = 3'd4;

    reg [2:0] state, next_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end

    always @(*) begin
        next_state = state;
        case (state)
            IDLE:  next_state = start      ? WASH  : IDLE;
            WASH:  next_state = cycle_done ? RINSE  : WASH;
            RINSE: next_state = cycle_done ? SPIN   : RINSE;
            SPIN:  next_state = cycle_done ? DONE   : SPIN;
            DONE:  next_state = IDLE;
            default: next_state = IDLE;
        endcase
    end

    always @(*) begin
        wash_on   = (state == WASH);
        rinse_on  = (state == RINSE);
        spin_on   = (state == SPIN);
        state_out = state;
    end
endmodule
