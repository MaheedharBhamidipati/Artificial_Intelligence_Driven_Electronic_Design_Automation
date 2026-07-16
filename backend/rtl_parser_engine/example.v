module adder(
    input a,
    input b,
    output sum
);

assign sum = a ^ b;

endmodule


module top(
    input x,
    input y,
    output z
);

wire temp;

adder u1(
    .a(x),
    .b(y),
    .sum(temp)
);

assign z = temp;

endmodule