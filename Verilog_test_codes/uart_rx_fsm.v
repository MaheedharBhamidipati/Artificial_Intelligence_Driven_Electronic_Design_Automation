module uart_rx_fsm (

    input clk,
    input rst,
    input rx,

    output reg rx_done

);

parameter IDLE  = 2'b00;
parameter START = 2'b01;
parameter DATA  = 2'b10;
parameter STOP  = 2'b11;

reg [1:0] state;
reg [1:0] next_state;


//==================================================
// STATE REGISTER
//==================================================

always @(posedge clk or posedge rst)
begin

    if (rst)
        state <= IDLE;

    else
        state <= next_state;

end


//==================================================
// NEXT STATE LOGIC
//==================================================

always @(*)
begin

    case(state)

        IDLE:
        begin

            if(rx == 1'b0)
                next_state = START;

            else
                next_state = IDLE;

        end

        START:
        begin

            if(rx == 1'b0)
                next_state = DATA;

            else
                next_state = IDLE;

        end

        DATA:
        begin

            if(rx == 1'b1)
                next_state = STOP;

            else
                next_state = DATA;

        end

        STOP:
        begin

            if(rx == 1'b1)
                next_state = IDLE;

            else
                next_state = START;

        end

        default:
            next_state = IDLE;

    endcase

end


//==================================================
// OUTPUT LOGIC
//==================================================

always @(*)
begin

    rx_done = 1'b0;

    case(state)

        STOP:
            rx_done = 1'b1;

        default:
            rx_done = 1'b0;

    endcase

end

endmodule