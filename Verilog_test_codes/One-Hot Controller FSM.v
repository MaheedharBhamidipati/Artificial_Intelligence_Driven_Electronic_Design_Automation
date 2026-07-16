module onehot_fsm (

    input clk,
    input rst,

    input start,
    input load_done,
    input exec_done,

    output reg finished

);

parameter IDLE = 4'b0001;
parameter LOAD = 4'b0010;
parameter EXEC = 4'b0100;
parameter DONE = 4'b1000;

reg [3:0] state;
reg [3:0] next_state;


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

            if(load_done)
                next_state = EXEC;

            else
                next_state = LOAD;

        end

        EXEC:
        begin

            if(exec_done)
                next_state = DONE;

            else
                next_state = EXEC;

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

    finished = 1'b0;

    case(state)

        DONE:
            finished = 1'b1;

        default:
            finished = 1'b0;

    endcase

end

endmodule