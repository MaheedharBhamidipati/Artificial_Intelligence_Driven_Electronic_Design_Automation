module alu_2bit (
    input  [1:0] A,
    input  [1:0] B,
    input  [2:0] ALU_Sel,
    output reg [1:0] Result,
    output reg CarryOut
);

always @(*) begin
    CarryOut = 1'b0;

    case (ALU_Sel)

        3'b000: {CarryOut, Result} = A + B; // Addition

        3'b001: {CarryOut, Result} = A - B; // Subtraction

        3'b010: Result = A & B;             // AND

        3'b011: Result = A | B;             // OR

        3'b100: Result = A ^ B;             // XOR

        3'b101: Result = ~A;                // NOT A

        3'b110: Result = A << 1;            // Shift Left

        3'b111: Result = A >> 1;            // Shift Right

        default: begin
            Result   = 2'b00;
            CarryOut = 1'b0;
        end

    endcase
end

endmodule