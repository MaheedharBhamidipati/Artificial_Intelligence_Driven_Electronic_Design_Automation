module moore_101101101_overlap (
    input  wire clk,
    input  wire rst,
    input  wire din,
    output reg  detected
);

    //==================================================
    // State Encoding
    //==================================================
    localparam S0 = 4'd0,
               S1 = 4'd1,
               S2 = 4'd2,
               S3 = 4'd3,
               S4 = 4'd4,
               S5 = 4'd5,
               S6 = 4'd6,
               S7 = 4'd7,
               S8 = 4'd8,
               S9 = 4'd9;

    reg [3:0] state;
    reg [3:0] next_state;

    //==================================================
    // State Register
    //==================================================
    always @(posedge clk or posedge rst) begin
        if (rst)
            state <= S0;
        else
            state <= next_state;
    end

    //==================================================
    // Next State Logic
    //==================================================
    always @(*) begin

        case(state)

            S0:
                if(din) next_state = S1;
                else    next_state = S0;

            S1:
                if(din) next_state = S1;
                else    next_state = S2;

            S2:
                if(din) next_state = S3;
                else    next_state = S0;

            S3:
                if(din) next_state = S4;
                else    next_state = S2;

            S4:
                if(din) next_state = S1;
                else    next_state = S5;

            S5:
                if(din) next_state = S6;
                else    next_state = S0;

            S6:
                if(din) next_state = S7;
                else    next_state = S2;

            S7:
                if(din) next_state = S1;
                else    next_state = S8;

            S8:
                if(din) next_state = S9;
                else    next_state = S0;

            //==================================================
            // DETECT STATE (OVERLAPPING)
            //==================================================
            S9:
                if(din)
                    next_state = S4;
                else
                    next_state = S2;

            default:
                next_state = S0;

        endcase

    end

    //==================================================
    // Moore Output Logic
    //==================================================
    always @(*) begin

        case(state)

            S9:      detected = 1'b1;

            default: detected = 1'b0;

        endcase

    end

endmodule