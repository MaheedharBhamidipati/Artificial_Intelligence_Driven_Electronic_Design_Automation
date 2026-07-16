module washing_machine_fsm (

    input clk,
    input rst,

    input start,
    input water_full,
    input wash_done,
    input rinse_done,
    input spin_done,

    output reg [2:0] status

);

parameter IDLE  = 3'b000;
parameter FILL  = 3'b001;
parameter WASH  = 3'b010;
parameter RINSE = 3'b011;
parameter SPIN  = 3'b100;
parameter DONE  = 3'b101;

reg [2:0] state;
reg [2:0] next_state;


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

            if(start)
                next_state = FILL;

            else
                next_state = IDLE;

        end

        FILL:
        begin

            if(water_full)
                next_state = WASH;

            else
                next_state = FILL;

        end

        WASH:
        begin

            if(wash_done)
                next_state = RINSE;

            else
                next_state = WASH;

        end

        RINSE:
        begin

            if(rinse_done)
                next_state = SPIN;

            else
                next_state = RINSE;

        end

        SPIN:
        begin

            if(spin_done)
                next_state = DONE;

            else
                next_state = SPIN;

        end

        DONE:
        begin

            next_state = IDLE;

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

    case(state)

        IDLE:
            status = 3'b000;

        FILL:
            status = 3'b001;

        WASH:
            status = 3'b010;

        RINSE:
            status = 3'b011;

        SPIN:
            status = 3'b100;

        DONE:
            status = 3'b101;

        default:
            status = 3'b000;

    endcase

end

endmodule