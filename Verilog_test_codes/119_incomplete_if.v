// Intentional RTL stress case: incomplete IF statement causing latch inference
module incomplete_if (
    input  wire       cond,
    input  wire [7:0] data_in,
    output reg  [7:0] data_out
);
    always @(*) begin
        if (cond) begin
            data_out = data_in;
        end
        // Missing else branch -> latch inferred
    end
endmodule
