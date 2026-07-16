module alu_4bit (
    input  [3:0] A,
    input  [3:0] B,
    input  [2:0] ALU_Sel,
    output reg [3:0] Result,
    output reg CarryOut
);

always @(*) begin
    CarryOut = 1'b0;

    case(ALU_Sel)

        3'b000: begin
            {CarryOut, Result} = A + B;   // Addition
        end

        3'b001: begin
            {CarryOut, Result} = A - B;   // Subtraction
        end

        3'b010: begin
            Result = A & B;               // AND
        end

        3'b011: begin
            Result = A | B;               // OR
        end

        3'b100: begin
            Result = A ^ B;               // XOR
        end

        3'b101: begin
            Result = ~A;                  // NOT
        end

        3'b110: begin
            Result = A << 1;              // Left Shift
        end

        3'b111: begin
            Result = A >> 1;              // Right Shift
        end

        default: begin
            Result = 4'b0000;
            CarryOut = 1'b0;
        end

    endcase
end

endmodule