module concat_test(
    input [1:0] A,
    input [1:0] B,
    output [7:0] Y
);

assign Y = {{2{A}}, {2{B}}};

endmodule