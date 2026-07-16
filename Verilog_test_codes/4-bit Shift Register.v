module shift_register (
    input clk,
    input din,
    output [3:0] q
);

wire q0, q1, q2, q3;

dff d1 (.clk(clk), .d(din), .q(q0));
dff d2 (.clk(clk), .d(q0),  .q(q1));
dff d3 (.clk(clk), .d(q1),  .q(q2));
dff d4 (.clk(clk), .d(q2),  .q(q3));

assign q = {q3, q2, q1, q0};

endmodule

module dff (
    input clk,
    input d,
    output reg q
);

always @(posedge clk)
    q <= d;

endmodule