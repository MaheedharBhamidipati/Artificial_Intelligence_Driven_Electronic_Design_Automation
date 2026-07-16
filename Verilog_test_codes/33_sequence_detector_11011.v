module sequence_detector_11011 (
    input  wire clk,
    input  wire rst_n,
    input  wire din,
    output reg  detected
);
    localparam S0=3'd0, S1=3'd1, S2=3'd2, S3=3'd3, S4=3'd4;
    reg [2:0] state, next_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= S0;
        else
            state <= next_state;
    end

    always @(*) begin
        case (state)
            S0: next_state = din ? S1 : S0;
            S1: next_state = din ? S2 : S0;
            S2: next_state = din ? S2 : S3;
            S3: next_state = din ? S4 : S0;
            S4: next_state = din ? S2 : S0; // overlap detection
            default: next_state = S0;
        endcase
    end

    always @(*) begin
        detected = (state == S4) && din;
    end
endmodule
