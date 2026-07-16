// Intentional RTL stress case: unused internal signals
module unused_signal (
    input  wire [7:0] a,
    input  wire [7:0] b,
    output wire [7:0] y
);
    wire [7:0] unused_sum;
    wire [7:0] unused_diff;
    reg        unused_flag;

    // These signals are computed/declared but never used downstream
    assign unused_sum  = a + b;
    assign unused_diff = a - b;

    initial unused_flag = 1'b0;

    assign y = a & b;
endmodule
