module mac_unit_v2 #(
    parameter WIDTH = 8
) (
    input  wire                clk,
    input  wire                rst_n,
    input  wire [WIDTH-1:0]    a,
    input  wire [WIDTH-1:0]    b,
    output reg  [2*WIDTH:0]    acc_out
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            acc_out <= {(2*WIDTH+1){1'b0}};
        else
            acc_out <= acc_out + (a * b);
    end
endmodule
