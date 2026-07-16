// Intentional RTL stress case: width mismatches between connected signals
module width_mismatch_sub (
    input  wire [3:0] in4,
    output wire [7:0] out8
);
    assign out8 = in4; // width mismatch: 4-bit driving 8-bit (implicit extension)
endmodule

module width_mismatch (
    input  wire [15:0] wide_in,
    output wire [3:0]  narrow_out
);
    wire [7:0] mid_signal;

    // width mismatch: connecting a 16-bit signal to a 4-bit port
    width_mismatch_sub u_sub (
        .in4(wide_in),
        .out8(mid_signal)
    );

    assign narrow_out = mid_signal; // width mismatch: 8-bit driving 4-bit (truncation)
endmodule
