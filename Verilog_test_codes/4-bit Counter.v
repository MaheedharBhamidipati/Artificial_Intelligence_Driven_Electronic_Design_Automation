module counter (
    input clk,
    input reset,
    output [3:0] count
);

reg [3:0] count_reg;

always @(posedge clk or posedge reset)
begin
    if (reset)
        count_reg <= 4'b0000;
    else
        count_reg <= count_reg + 1;
end

assign count = count_reg;

endmodule