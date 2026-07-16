module gray2bin #(
    parameter WIDTH = 4
) (
    input  wire [WIDTH-1:0] gray,
    output reg  [WIDTH-1:0] bin
);
    integer i;
    always @(*) begin
        bin[WIDTH-1] = gray[WIDTH-1];
        for (i = WIDTH-2; i >= 0; i = i - 1) begin
            bin[i] = bin[i+1] ^ gray[i];
        end
    end
endmodule
