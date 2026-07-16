module sequence_detector_1010_mealy_overlap (

    input clk,
    input rst,
    input din,

    output reg detected

);

parameter S0 = 2'b00;
parameter S1 = 2'b01;
parameter S2 = 2'b10;
parameter S3 = 2'b11;

reg [1:0] state;
reg [1:0] next_state;


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
                next_state = S2;   // Overlapping transition
        end

        default:
            next_state = S0;

    endcase

end


// Mealy Output Logic

always @(*)
begin

    detected = 1'b0;

    if(state == S3 && din == 1'b0)
        detected = 1'b1;

end

endmodule