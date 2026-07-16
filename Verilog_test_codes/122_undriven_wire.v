// Intentional RTL stress case: declared wire that is never driven
module undriven_wire (
    input  wire       a,
    input  wire       b,
    output wire       y
);
    wire dangling_wire; // declared but never assigned/driven

    assign y = a & b;
    // 'dangling_wire' is intentionally left unconnected/undriven
endmodule
