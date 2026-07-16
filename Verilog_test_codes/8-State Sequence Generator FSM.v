module seq8_fsm (
    input clk,
    input rst,
    output reg [2:0] seq_out
);

reg [2:0] state;

parameter S0 = 0;
parameter S1 = 1;
parameter S2 = 2;
parameter S3 = 3;
parameter S4 = 4;
parameter S5 = 5;
parameter S6 = 6;
parameter S7 = 7;

always @(posedge clk or posedge rst)
begin

    if(rst)
        state <= S0;
    else begin

        case(state)

            S0: state <= S1;
            S1: state <= S2;
            S2: state <= S3;
            S3: state <= S4;
            S4: state <= S5;
            S5: state <= S6;
            S6: state <= S7;
            S7: state <= S0;

            default:
                state <= S0;

        endcase
    end
end

always @(*)
begin
    seq_out = state;
end

endmodule