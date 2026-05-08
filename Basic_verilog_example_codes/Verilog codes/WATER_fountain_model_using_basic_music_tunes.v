// =======================================================
//			PWM GENERATOR (REGISTERED INPUT)
// =======================================================

module pwm_generator (
    input clk,
    input [7:0] duty,
    output reg pwm
);

reg [7:0] counter = 0;
reg [7:0] duty_reg;

always @(posedge clk) begin
    duty_reg <= duty;               // ? Register input (timing fix)
    counter <= counter + 1;
    pwm <= (counter < duty_reg);
end

endmodule


// =======================================================
//		 BAND SPLITTER (COMBINATIONAL)
// =======================================================

module band_splitter (
    input [11:0] audio_in,
    output reg [7:0] A, B, C, D
);

always @(*) begin
    A = 0; B = 0; C = 0; D = 0;

    if (audio_in < 12'd1024)
        A = audio_in[11:4];
    else if (audio_in < 12'd2048)
        B = audio_in[11:4];
    else if (audio_in < 12'd3072)
        C = audio_in[11:4];
    else
        D = audio_in[11:4];
end

endmodule


// =======================================================
// 		SUB-BAND SPLITTER (COMBINATIONAL)
// =======================================================

module subband_splitter (
    input clk,
    input [7:0] in,
    output reg [7:0] s1, s2, s3
);

reg [15:0] mult1, mult2;

always @(posedge clk) begin
    mult1 <= in * 8'd85;
    mult2 <= in * 8'd170;

    s1 <= mult1 >> 8;
    s2 <= mult2 >> 8;
    s3 <= in;
end

endmodule


// =======================================================
// 			 TOP MODULE (PIPELINED)
// =======================================================

module musical_fountain_top (
    input clk,
    input [11:0] audio_in,
    output [11:0] pwm_out
);

// =====================
// Stage 1: Band Split
// =====================
wire [7:0] A_c, B_c, C_c, D_c;

// Registered outputs (Pipeline Stage 1)
reg [7:0] A_r, B_r, C_r, D_r;

band_splitter bs (
    .audio_in(audio_in),
    .A(A_c), .B(B_c), .C(C_c), .D(D_c)
);

always @(posedge clk) begin
    A_r <= A_c;
    B_r <= B_c;
    C_r <= C_c;
    D_r <= D_c;
end


// =====================
// Stage 2: Subband Split
// =====================
wire [7:0] A1_c,A2_c,A3_c;
wire [7:0] B1_c,B2_c,B3_c;
wire [7:0] C1_c,C2_c,C3_c;
wire [7:0] D1_c,D2_c,D3_c;

// Registered outputs (Pipeline Stage 2)
reg [7:0] A1_r,A2_r,A3_r;
reg [7:0] B1_r,B2_r,B3_r;
reg [7:0] C1_r,C2_r,C3_r;
reg [7:0] D1_r,D2_r,D3_r;

subband_splitter sA (clk, A_r, A1_c, A2_c, A3_c);
subband_splitter sB (clk, B_r, B1_c, B2_c, B3_c);
subband_splitter sC (clk, C_r, C1_c, C2_c, C3_c);
subband_splitter sD (clk, D_r, D1_c, D2_c, D3_c);

always @(posedge clk) begin
    A1_r <= A1_c; A2_r <= A2_c; A3_r <= A3_c;
    B1_r <= B1_c; B2_r <= B2_c; B3_r <= B3_c;
    C1_r <= C1_c; C2_r <= C2_c; C3_r <= C3_c;
    D1_r <= D1_c; D2_r <= D2_c; D3_r <= D3_c;
end


// ================================
// Stage 3: PWM Generation
// ================================
pwm_generator p0 (clk, A1_r, pwm_out[0]);
pwm_generator p1 (clk, A2_r, pwm_out[1]);
pwm_generator p2 (clk, A3_r, pwm_out[2]);

pwm_generator p3 (clk, B1_r, pwm_out[3]);
pwm_generator p4 (clk, B2_r, pwm_out[4]);
pwm_generator p5 (clk, B3_r, pwm_out[5]);

pwm_generator p6 (clk, C1_r, pwm_out[6]);
pwm_generator p7 (clk, C2_r, pwm_out[7]);
pwm_generator p8 (clk, C3_r, pwm_out[8]);

pwm_generator p9  (clk, D1_r, pwm_out[9]);
pwm_generator p10 (clk, D2_r, pwm_out[10]);
pwm_generator p11 (clk, D3_r, pwm_out[11]);

endmodule