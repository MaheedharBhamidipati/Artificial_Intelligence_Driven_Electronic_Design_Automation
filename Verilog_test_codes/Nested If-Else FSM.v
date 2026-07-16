module nested_if_fsm (
    input clk,
    input rst,
    input start,
    output reg done
);

reg [1:0] state;

parameter IDLE = 2'b00;
parameter RUN  = 2'b01;
parameter DONE = 2'b10;

always @(posedge clk or posedge rst)
begin
    if(rst)
        state <= IDLE;
    else begin

        if(state == IDLE) begin
            if(start)
                state <= RUN;
            else
                state <= IDLE;
        end

        else if(state == RUN)
            state <= DONE;

        else if(state == DONE)
            state <= IDLE;

        else
            state <= IDLE;
    end
end

always @(*)
begin
    done = (state == DONE);
end

endmodule