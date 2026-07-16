module all_colors_fsm (

    input clk,
    input rst,
    input start,
    input finish,

    output reg done

);

parameter IDLE = 3'b000;
parameter LOAD = 3'b001;
parameter EXEC = 3'b010;
parameter DONE = 3'b011;
parameter ERROR = 3'b100;

reg [2:0] state;
reg [2:0] next_state;


//==================================================
// STATE REGISTER
//==================================================

always @(posedge clk or posedge rst)
begin

    if(rst)
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
                next_state = LOAD;

            else
                next_state = IDLE;

        end

        LOAD:
        begin

            next_state = EXEC;

        end

        EXEC:
        begin

            if(finish)
                next_state = DONE;

            else
                next_state = EXEC;
        end

        DONE:
        begin

            next_state = ERROR;
        end

        ERROR:
        begin

            next_state = ERROR;
        end

        default:
            next_state = ERROR;

    endcase

end


//==================================================
// OUTPUT LOGIC
//==================================================

always @(*)
begin

    done = (state == DONE);

end

endmodule