// Intentional RTL stress case: incomplete combinational assignment
// infers a latch on 'q' because not all branches assign it.
module inferred_latch (
    input  wire       en,
    input  wire [1:0] sel,
    input  wire [7:0] a,
    input  wire [7:0] b,
    output reg  [7:0] q
);
    always @(*) begin
        if (en) begin
            case (sel)
                2'b00: q = a;
                2'b01: q = b;
                // Missing 2'b10, 2'b11, and no default -> latch inferred
            endcase
        end
        // Missing else branch -> latch inferred when en == 0
    end
endmodule
