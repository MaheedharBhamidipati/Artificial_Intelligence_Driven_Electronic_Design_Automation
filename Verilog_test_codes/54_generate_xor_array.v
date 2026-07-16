module generate_xor_array #(
    parameter WIDTH = 8,
    parameter NUM   = 4
) (
    input  wire [NUM-1:0][WIDTH-1:0] a,
    input  wire [NUM-1:0][WIDTH-1:0] b,
    output wire [NUM-1:0][WIDTH-1:0] y
);
    genvar i;
    generate
        for (i = 0; i < NUM; i = i + 1) begin : xor_gen
            assign y[i] = a[i] ^ b[i];
        end
    endgenerate
endmodule
