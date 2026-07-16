module mealy_101101101_overlap (
    input clk,
    input rst,
    input din,
    output reg detected
);

    reg [3:0] state;

    localparam S0 = 4'd0,
               S1 = 4'd1,
               S2 = 4'd2,
               S3 = 4'd3,
               S4 = 4'd4,
               S5 = 4'd5,
               S6 = 4'd6,
               S7 = 4'd7,
               S8 = 4'd8;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state <= S0;
            detected <= 1'b0;
        end
        else begin
            detected <= 1'b0;

            case(state)

                S0: begin
                    if(din) state <= S1;
                    else    state <= S0;
                end

                S1: begin
                    if(din) state <= S1;
                    else    state <= S2;
                end

                S2: begin
                    if(din) state <= S3;
                    else    state <= S0;
                end

                S3: begin
                    if(din) state <= S4;
                    else    state <= S2;
                end

                S4: begin
                    if(din) state <= S1;
                    else    state <= S5;
                end

                S5: begin
                    if(din) state <= S6;
                    else    state <= S0;
                end

                S6: begin
                    if(din) state <= S7;
                    else    state <= S2;
                end

                S7: begin
                    if(din) state <= S1;
                    else    state <= S8;
                end

                S8: begin
                    if(din) begin
                        detected <= 1'b1;
                        state <= S4;   // overlap transition
                    end
                    else begin
                        state <= S0;
                    end
                end

                default: state <= S0;

            endcase
        end
    end

endmodule