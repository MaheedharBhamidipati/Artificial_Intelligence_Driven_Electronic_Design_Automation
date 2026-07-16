module mac_unit #(
    parameter WIDTH = 8
) (
    input  wire                   clk,
    input  wire                   rst_n,
    input  wire                   clear_acc,
    input  wire [WIDTH-1:0]       a,
    input  wire [WIDTH-1:0]       b,
    output reg  [2*WIDTH:0]       acc
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            acc <= {(2*WIDTH+1){1'b0}};
        else if (clear_acc)
            acc <= {(2*WIDTH+1){1'b0}};
        else
            acc <= acc + (a * b);
    end
endmodule
