module mixed_logic_fsm (
    input clk,
    input rst,
    input start,
    output reg busy,
    output reg done
);

reg [1:0] state;
reg [1:0] next_state;

parameter IDLE = 0;
parameter RUN  = 1;
parameter DONE = 2;

always @(posedge clk or posedge rst)
begin
    if(rst)
        state <= IDLE;
    else
        state <= next_state;
end

always @(*)
begin

    busy = 0;
    done = 0;

    case(state)

        IDLE:
        begin
            busy = 0;
            done = 0;

            if(start)
                next_state = RUN;
            else
                next_state = IDLE;
        end

        RUN:
        begin
            busy = 1;
            done = 0;
            next_state = DONE;
        end

        DONE:
        begin
            busy = 0;
            done = 1;
            next_state = IDLE;
        end

        default:
            next_state = IDLE;

    endcase
end

endmodule