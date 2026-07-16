module moore_101101101_nonoverlap (
    input  wire clk,
    input  wire rst,
    input  wire din,
    output reg  detected
);

    //==================================================
    // State Encoding
    //==================================================
    localparam S0 = 4'd0,  // Initial
               S1 = 4'd1,  // 1
               S2 = 4'd2,  // 10
               S3 = 4'd3,  // 101
               S4 = 4'd4,  // 1011
               S5 = 4'd5,  // 10110
               S6 = 4'd6,  // 101101
               S7 = 4'd7,  // 1011011
               S8 = 4'd8,  // 10110110
               S9 = 4'd9;  // 101101101 (Detected)

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

            S0: begin
                if (din)
                    next_state = S1;
                else
                    next_state = S0;
            end

            S1: begin
                if (din)
                    next_state = S1;
                else
                    next_state = S2;
            end

            S2: begin
                if (din)
                    next_state = S3;
                else
                    next_state = S0;
            end

            S3: begin
                if (din)
                    next_state = S4;
                else
                    next_state = S2;
            end

            S4: begin
                if (din)
                    next_state = S1;
                else
                    next_state = S5;
            end

            S5: begin
                if (din)
                    next_state = S6;
                else
                    next_state = S0;
            end

            S6: begin
                if (din)
                    next_state = S7;
                else
                    next_state = S2;
            end

            S7: begin
                if (din)
                    next_state = S1;
                else
                    next_state = S8;
            end

            S8: begin
                if (din)
                    next_state = S9;
                else
                    next_state = S0;
            end

            // Detection State
            S9: begin
                next_state = S0;
            end

            default: begin
                next_state = S0;
            end

        endcase
    end

    //==================================================
    // Output Logic (Moore)
    //==================================================
    always @(*) begin

        case(state)

            S9:
                detected = 1'b1;

            default:
                detected = 1'b0;

        endcase

    end

endmodule