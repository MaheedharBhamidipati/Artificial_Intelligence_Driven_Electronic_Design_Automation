module COMB_LOGIC_TEST (
    input  [1:0] A,
    input  [1:0] B,
    input        SEL,
    input        CIN,
    output reg [2:0] SUM,
    output reg       EQ,
    output           PARITY
);

    // Continuous assignment with a reduction operator
    assign PARITY = ^{A, B, SEL, CIN};

    // always block with case statement + arithmetic
    always @(*) begin
        case (SEL)
            1'b0: SUM = A + B + CIN;
            1'b1: SUM = A - B;
            default: SUM = 3'b000;
        endcase
    end

    // always block with if-else + comparison
    always @(*) begin
        if (A == B)
            EQ = 1'b1;
        else
            EQ = 1'b0;
    end

endmodule