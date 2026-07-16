module nand_gate (
    input  wire a,
    input  wire b,
    output wire y
);
    assign y = ~(a & b);
endmodule

module full_adder_nand (
    input  wire a,
    input  wire b,
    input  wire cin,
    output wire sum,
    output wire cout
);
    wire n1, n2, n3, n4, n5, n6, n7, n8, n9;

    nand_gate g1 (.a(a),  .b(b),  .y(n1));
    nand_gate g2 (.a(a),  .b(n1), .y(n2));
    nand_gate g3 (.a(b),  .b(n1), .y(n3));
    nand_gate g4 (.a(n2), .b(n3), .y(n4));
    nand_gate g5 (.a(n4), .b(cin), .y(n5));
    nand_gate g6 (.a(n4), .b(n5), .y(n6));
    nand_gate g7 (.a(cin), .b(n5), .y(n7));
    nand_gate g8 (.a(n6), .b(n7), .y(sum));
    nand_gate g9 (.a(n5), .b(n1), .y(n8));
    nand_gate g10(.a(n8), .b(n8), .y(n9));
    assign cout = ~n9;
endmodule

module ripple_carry_adder_nand (
    input  wire [3:0] a,
    input  wire [3:0] b,
    input  wire        cin,
    output wire [3:0] sum,
    output wire        cout
);
    wire [3:0] carry;

    full_adder_nand fa0 (.a(a[0]), .b(b[0]), .cin(cin),      .sum(sum[0]), .cout(carry[0]));
    full_adder_nand fa1 (.a(a[1]), .b(b[1]), .cin(carry[0]), .sum(sum[1]), .cout(carry[1]));
    full_adder_nand fa2 (.a(a[2]), .b(b[2]), .cin(carry[1]), .sum(sum[2]), .cout(carry[2]));
    full_adder_nand fa3 (.a(a[3]), .b(b[3]), .cin(carry[2]), .sum(sum[3]), .cout(cout));
endmodule
