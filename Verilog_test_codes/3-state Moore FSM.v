module simple_fsm (
    input clk,
    input rst,
    input start,
    input done,
    output reg finished
);

parameter IDLE = 2'b00;
parameter RUN  = 2'b01;
parameter STOP = 2'b10;

reg [1:0] state;
reg [1:0] next_state;

always @(posedge clk or posedge rst)
begin
    if (rst)
        state <= IDLE;
    else
        state <= next_state;
end

always @(*)
begin

    case(state)

        IDLE:
        begin
            if(start)
                next_state = RUN;
            else
                next_state = IDLE;
        end

        RUN:
        begin
            if(done)
                next_state = STOP;
            else
                next_state = RUN;
        end

        STOP:
        begin
            next_state = IDLE;
        end

        default:
            next_state = IDLE;

    endcase

end

always @(*)
begin

    finished = 0;

    case(state)

        IDLE:
            finished = 0;

        RUN:
            finished = 0;

        STOP:
            finished = 1;

    endcase

end

endmodule