module carry_lookahead_adder_4bit (
    input  [3:0] A,
    input  [3:0] B,
    input  Cin,
    output [3:0] Sum,
    output Cout
);

wire [3:0] G, P;   // Generate and Propagate
wire C1, C2, C3;

// Step 1: Generate & Propagate
assign G = A & B;        // Generate
assign P = A ^ B;        // Propagate

// Step 2: Carry Lookahead Logic
assign C1 = G[0] | (P[0] & Cin);
assign C2 = G[1] | (P[1] & G[0]) | (P[1] & P[0] & Cin);
assign C3 = G[2] | (P[2] & G[1]) | (P[2] & P[1] & G[0]) 
                      | (P[2] & P[1] & P[0] & Cin);
assign Cout = G[3] | (P[3] & G[2]) | (P[3] & P[2] & G[1]) 
                       | (P[3] & P[2] & P[1] & G[0]) 
                       | (P[3] & P[2] & P[1] & P[0] & Cin);

// Step 3: Sum Calculation
assign Sum = P ^ {C3, C2, C1, Cin};

endmodule