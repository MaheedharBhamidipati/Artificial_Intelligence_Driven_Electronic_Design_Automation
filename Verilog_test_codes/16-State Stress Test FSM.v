module fsm16 (
    input clk,
    input rst
);

reg [3:0] state;

parameter S0  = 4'd0;
parameter S1  = 4'd1;
parameter S2  = 4'd2;
parameter S3  = 4'd3;
parameter S4  = 4'd4;
parameter S5  = 4'd5;
parameter S6  = 4'd6;
parameter S7  = 4'd7;
parameter S8  = 4'd8;
parameter S9  = 4'd9;
parameter S10 = 4'd10;
parameter S11 = 4'd11;
parameter S12 = 4'd12;
parameter S13 = 4'd13;
parameter S14 = 4'd14;
parameter S15 = 4'd15;

always @(posedge clk or posedge rst)
begin

    if(rst)
        state <= S0;

    else begin

        case(state)

            S0  : state <= S1;
            S1  : state <= S2;
            S2  : state <= S3;
            S3  : state <= S4;
            S4  : state <= S5;
            S5  : state <= S6;
            S6  : state <= S7;
            S7  : state <= S8;
            S8  : state <= S9;
            S9  : state <= S10;
            S10 : state <= S11;
            S11 : state <= S12;
            S12 : state <= S13;
            S13 : state <= S14;
            S14 : state <= S15;
            S15 : state <= S0;

            default:
                state <= S0;

        endcase
    end
end

endmodule