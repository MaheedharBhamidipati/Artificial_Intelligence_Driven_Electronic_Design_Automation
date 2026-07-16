module dff (
    input clk,
    input d,
    output q
);

wire n1, n2, n3, n4;

nand (n1, d, clk);
nand (n2, n1, clk);

nand (n3, n2, n4);
nand (n4, n3, clk);

nand (q, n3, q);

endmodule