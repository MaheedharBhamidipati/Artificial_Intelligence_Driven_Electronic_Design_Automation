module alu (
    input  [7:0] A,
    input  [7:0] B,
    input  [3:0] ALU_Sel,
    output reg [7:0] ALU_Out,
    output reg CarryOut
);

always @(*) begin
    CarryOut = 0;

    case (ALU_Sel)

        4'b0000: begin
            {CarryOut, ALU_Out} = A + B;      // Addition
        end

        4'b0001: begin
            {CarryOut, ALU_Out} = A - B;      // Subtraction
        end

        4'b0010: ALU_Out = A & B;             // AND

        4'b0011: ALU_Out = A | B;             // OR

        4'b0100: ALU_Out = A ^ B;             // XOR

        4'b0101: ALU_Out = ~(A | B);          // NOR

        4'b0110: ALU_Out = ~(A & B);          // NAND

        4'b0111: ALU_Out = ~(A ^ B);          // XNOR

        4'b1000: ALU_Out = A << 1;            // Shift Left

        4'b1001: ALU_Out = A >> 1;            // Shift Right

        4'b1010: ALU_Out = (A > B) ? 8'd1 : 8'd0; // Greater Than

        4'b1011: ALU_Out = (A == B) ? 8'd1 : 8'd0; // Equal

        4'b1100: ALU_Out = A + 1;             // Increment

        4'b1101: ALU_Out = A - 1;             // Decrement

        4'b1110: ALU_Out = ~A;                // NOT A

        4'b1111: ALU_Out = 8'd0;              // Clear

        default: ALU_Out = 8'd0;

    endcase
end

endmodule