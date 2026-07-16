// ============================================================
// FULL ADDER
// ============================================================

module full_adder(

    input  A,
    input  B,
    input  CIN,

    output SUM,
    output COUT
);

    wire axb;
    wire w1;
    wire w2;

    assign axb  = A ^ B;

    assign SUM  = axb ^ CIN;

    assign w1   = A & B;

    assign w2   = axb & CIN;

    assign COUT = w1 | w2;

endmodule

// ============================================================
// 4-BIT RIPPLE CARRY ADDER
// ============================================================

module ripple_carry_adder_4bit(

    input  [3:0] A,
    input  [3:0] B,
    input        CIN,

    output [3:0] SUM,
    output       COUT
);

    wire C1;
    wire C2;
    wire C3;

    // ========================================================
    // FULL ADDER STAGE 0
    // ========================================================

    full_adder FA0 (

        .A   (A[0]),
        .B   (B[0]),
        .CIN (CIN),

        .SUM (SUM[0]),
        .COUT(C1)
    );

    // ========================================================
    // FULL ADDER STAGE 1
    // ========================================================

    full_adder FA1 (

        .A   (A[1]),
        .B   (B[1]),
        .CIN (C1),

        .SUM (SUM[1]),
        .COUT(C2)
    );

    // ========================================================
    // FULL ADDER STAGE 2
    // ========================================================

    full_adder FA2 (

        .A   (A[2]),
        .B   (B[2]),
        .CIN (C2),

        .SUM (SUM[2]),
        .COUT(C3)
    );

    // ========================================================
    // FULL ADDER STAGE 3
    // ========================================================

    full_adder FA3 (

        .A   (A[3]),
        .B   (B[3]),
        .CIN (C3),

        .SUM (SUM[3]),
        .COUT(COUT)
    );

endmodule