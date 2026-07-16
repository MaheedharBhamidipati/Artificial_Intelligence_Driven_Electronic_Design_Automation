module sequence_generator_fsm_8state (
    input  wire       clk,
    input  wire       rst_n,
    output reg  [2:0] state,
    output reg        seq_out
);
    localparam S0=3'd0, S1=3'd1, S2=3'd2, S3=3'd3,
               S4=3'd4, S5=3'd5, S6=3'd6, S7=3'd7;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S0;
        else begin
            case (state)
                S0: state <= S1;
                S1: state <= S2;
                S2: state <= S3;
                S3: state <= S4;
                S4: state <= S5;
                S5: state <= S6;
                S6: state <= S7;
                S7: state <= S0;
                default: state <= S0;
            endcase
        end
    end

    always @(*) begin
        case (state)
            S0: seq_out = 1'b1;
            S1: seq_out = 1'b0;
            S2: seq_out = 1'b1;
            S3: seq_out = 1'b1;
            S4: seq_out = 1'b0;
            S5: seq_out = 1'b0;
            S6: seq_out = 1'b1;
            S7: seq_out = 1'b0;
            default: seq_out = 1'b0;
        endcase
    end
endmodule
