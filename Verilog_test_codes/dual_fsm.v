module dual_fsm (
    input clk,
    input rst,
    input start
);

reg [1:0] state_a;
reg [1:0] state_b;

parameter A_IDLE = 0;
parameter A_RUN  = 1;

parameter B_WAIT = 0;
parameter B_DONE = 1;

always @(posedge clk or posedge rst)
begin

    if(rst)
        state_a <= A_IDLE;

    else begin

        case(state_a)

            A_IDLE:
                if(start)
                    state_a <= A_RUN;

            A_RUN:
                state_a <= A_IDLE;

        endcase
    end
end

always @(posedge clk or posedge rst)
begin

    if(rst)
        state_b <= B_WAIT;

    else begin

        case(state_b)

            B_WAIT:
                state_b <= B_DONE;

            B_DONE:
                state_b <= B_WAIT;

        endcase
    end
end

endmodule