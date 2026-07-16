module mixed_signed_unsigned #(
    parameter WIDTH = 8
) (
    input  wire signed [WIDTH-1:0]   signed_a,
    input  wire        [WIDTH-1:0]   unsigned_b,
    output wire signed [WIDTH:0]     mixed_sum,
    output wire         [WIDTH:0]    unsigned_sum
);
    // Mixing signed and unsigned operands: unsigned_b is treated as unsigned
    // in the signed context per Verilog rules, demonstrating a common pitfall.
    assign mixed_sum    = signed_a + $signed({1'b0, unsigned_b});
    assign unsigned_sum = $unsigned(signed_a) + unsigned_b;
endmodule
