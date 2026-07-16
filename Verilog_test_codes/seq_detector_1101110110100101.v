module mealy_1101110110100101_nonoverlap(
    input clk,
    input rst,
    input x,
    output reg z
);

reg [4:0] state;
reg [4:0] next_state;

parameter
A = 5'd0,
B = 5'd1,
C = 5'd2,
D = 5'd3,
E = 5'd4,
F = 5'd5,
G = 5'd6,
H = 5'd7,
I = 5'd8,
J = 5'd9,
K = 5'd10,
L = 5'd11,
M = 5'd12,
N = 5'd13,
O = 5'd14,
P = 5'd15;

//====================================================
// State Register
//====================================================

always @(posedge clk or posedge rst)
begin
    if(rst)
        state <= A;
    else
        state <= next_state;
end

//====================================================
// Next State Logic
//====================================================

always @(*)
begin

    z = 1'b0;

    case(state)

        A:
        begin
            if(x)
                next_state = B;
            else
                next_state = A;
        end

        B:
        begin
            if(x)
                next_state = C;
            else
                next_state = A;
        end

        C:
        begin
            if(x)
                next_state = C;
            else
                next_state = D;
        end

        D:
        begin
            if(x)
                next_state = E;
            else
                next_state = A;
        end

        E:
        begin
            if(x)
                next_state = F;
            else
                next_state = A;
        end

        F:
        begin
            if(x)
                next_state = G;
            else
                next_state = A;
        end

        G:
        begin
            if(x)
                next_state = C;
            else
                next_state = H;
        end

        H:
        begin
            if(x)
                next_state = I;
            else
                next_state = A;
        end

        I:
        begin
            if(x)
                next_state = J;
            else
                next_state = A;
        end

        J:
        begin
            if(x)
                next_state = C;
            else
                next_state = K;
        end

        K:
        begin
            if(x)
                next_state = L;
            else
                next_state = A;
        end

        L:
        begin
            if(x)
                next_state = C;
            else
                next_state = M;
        end

        M:
        begin
            if(x)
                next_state = A;
            else
                next_state = N;
        end

        N:
        begin
            if(x)
                next_state = O;
            else
                next_state = A;
        end

        O:
        begin
            if(x)
                next_state = P;
            else
                next_state = A;
        end

        P:
        begin
            if(x)
            begin
                next_state = A;
                z = 1'b1;      // Sequence Detected
            end
            else
                next_state = A;
        end

        default:
        begin
            next_state = A;
            z = 1'b0;
        end

    endcase

end

endmodule