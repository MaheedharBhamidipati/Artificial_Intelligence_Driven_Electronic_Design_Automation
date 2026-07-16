module sequence_detector (
    input clk,
    input reset,
    input x,
    output z
);

reg [1:0] state;

parameter S0 = 2'b00,
          S1 = 2'b01,
          S2 = 2'b10;

always @(posedge clk or posedge reset)
begin
    if (reset)
        state <= S0;
    else
    begin
        case(state)

            S0:
                if(x)
                    state <= S1;
                else
                    state <= S0;

            S1:
                if(x)
                    state <= S1;
                else
                    state <= S2;

            S2:
                if(x)
                    state <= S1;
                else
                    state <= S0;

            default:
                state <= S0;

        endcase
    end
end

assign z = (state == S2);

endmodule