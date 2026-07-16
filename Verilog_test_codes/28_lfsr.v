module lfsr #(
    parameter WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    output reg  [WIDTH-1:0] lfsr_out
);
    wire feedback;
    assign feedback = lfsr_out[WIDTH-1] ^ lfsr_out[WIDTH-2] ^ lfsr_out[WIDTH-3] ^ lfsr_out[WIDTH-4] ^ ~|lfsr_out;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            lfsr_out <= {{(WIDTH-1){1'b0}}, 1'b1};
        else
            lfsr_out <= {lfsr_out[WIDTH-2:0], feedback};
    end
endmodule
