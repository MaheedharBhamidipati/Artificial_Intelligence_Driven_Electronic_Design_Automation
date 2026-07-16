module priority_encoder #(
    parameter WIDTH     = 8,
    parameter CODE_WIDTH = $clog2(WIDTH)
) (
    input  wire [WIDTH-1:0]      req,
    output reg  [CODE_WIDTH-1:0] code,
    output reg                   valid
);
    integer i;
    always @(*) begin
        code  = {CODE_WIDTH{1'b0}};
        valid = 1'b0;
        for (i = WIDTH-1; i >= 0; i = i - 1) begin
            if (req[i] && !valid) begin
                code  = i[CODE_WIDTH-1:0];
                valid = 1'b1;
            end
        end
    end
endmodule
