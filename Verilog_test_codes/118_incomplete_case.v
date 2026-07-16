// Intentional RTL stress case: CASE statement without a default branch
module incomplete_case (
    input  wire [1:0] sel,
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire [7:0] c,
    output reg  [7:0] result
);
    always @(*) begin
        case (sel)
            2'b00: result = a;
            2'b01: result = b;
            2'b10: result = c;
            // No 2'b11 case and no default branch
        endcase
    end
endmodule
