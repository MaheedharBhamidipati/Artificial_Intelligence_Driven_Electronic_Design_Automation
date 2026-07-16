module sequence_detector_1010_moore (

    input clk,
    input rst,
    input din,

    output reg detected

);

parameter S0 = 3'b000;  // Initial
parameter S1 = 3'b001;  // 1
parameter S2 = 3'b010;  // 10
parameter S3 = 3'b011;  // 101
parameter S4 = 3'b100;  // 1010 Detected

reg [2:0] state;
reg [2:0] next_state;



// State Register

always @(posedge clk or posedge rst)
begin

    if (rst)
        state <= S0;

    else
        state <= next_state;

end



// Next State Logic

always @(*)
begin

    case(state)

        S0:
        begin
            if(din)
                next_state = S1;
            else
                next_state = S0;
        end

        S1:
        begin
            if(din)
                next_state = S1;
            else
                next_state = S2;
        end

        S2:
        begin
            if(din)
                next_state = S3;
            else
                next_state = S0;
        end

        S3:
        begin
            if(din)
                next_state = S1;
            else
                next_state = S4;
        end

        S4:
        begin
            if(din)
                next_state = S1;
            else
                next_state = S0;
        end

        default:
            next_state = S0;

    endcase

end



// Moore Output Logic

always @(*)
begin

    case(state)

        S4:
            detected = 1'b1;

        default:
            detected = 1'b0;

    endcase

end

endmodule