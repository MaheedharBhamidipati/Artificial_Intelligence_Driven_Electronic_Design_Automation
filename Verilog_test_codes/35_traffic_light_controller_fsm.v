module traffic_light_controller_fsm (
    input  wire       clk,
    input  wire       rst_n,
    output reg  [2:0] light // {red, yellow, green}
);
    localparam S_GREEN  = 2'd0;
    localparam S_YELLOW = 2'd1;
    localparam S_RED    = 2'd2;

    reg [1:0]  state, next_state;
    reg [7:0]  timer;
    localparam GREEN_TIME  = 8'd100;
    localparam YELLOW_TIME = 8'd20;
    localparam RED_TIME    = 8'd100;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= S_RED;
            timer <= 8'd0;
        end else begin
            if (timer == 8'd0) begin
                state <= next_state;
                case (next_state)
                    S_GREEN:  timer <= GREEN_TIME;
                    S_YELLOW: timer <= YELLOW_TIME;
                    S_RED:    timer <= RED_TIME;
                    default:  timer <= RED_TIME;
                endcase
            end else begin
                timer <= timer - 8'd1;
            end
        end
    end

    always @(*) begin
        case (state)
            S_GREEN:  next_state = S_YELLOW;
            S_YELLOW: next_state = S_RED;
            S_RED:    next_state = S_GREEN;
            default:  next_state = S_RED;
        endcase
    end

    always @(*) begin
        case (state)
            S_GREEN:  light = 3'b001;
            S_YELLOW: light = 3'b010;
            S_RED:    light = 3'b100;
            default:  light = 3'b100;
        endcase
    end
endmodule
