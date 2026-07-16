module combinational_stress(
    input [3:0] A,
    input [3:0] B,
    input sel,
    output [3:0] Y,
    output gt,
    output parity
);

wire [3:0] sum;
wire [3:0] and_out;

assign sum     = A + B;
assign and_out = A & B;

assign Y = sel ? sum : and_out;

assign gt = (A > B);

assign parity = ^Y;

endmodule