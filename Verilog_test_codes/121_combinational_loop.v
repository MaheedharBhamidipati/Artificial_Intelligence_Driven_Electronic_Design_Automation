// Intentional RTL stress case: combinational feedback loop
module combinational_loop (
    input  wire       a,
    output wire       y
);
    wire b;

    // y depends on b, and b depends on y -> combinational loop
    assign y = a ^ b;
    assign b = y & a;
endmodule
