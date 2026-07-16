module vending_machine(

    input clk,
    input rst,
    input coin,

    output reg dispense

);

parameter IDLE    = 2'b00;
parameter ONECOIN = 2'b01;
parameter VEND    = 2'b10;

reg [1:0] state;
reg [1:0] next_state;

always @(posedge clk or posedge rst)
begin

    if(rst)
        state <= IDLE;

    else
        state <= next_state;

end

always @(*)
begin

    case(state)

        IDLE:

            if(coin)
                next_state = ONECOIN;
            else
                next_state = IDLE;

        ONECOIN:

            if(coin)
                next_state = VEND;
            else
                next_state = ONECOIN;

        VEND:
            next_state = IDLE;

        default:
            next_state = IDLE;

    endcase

end

always @(*)
begin

    dispense = (state == VEND);

end

endmodule