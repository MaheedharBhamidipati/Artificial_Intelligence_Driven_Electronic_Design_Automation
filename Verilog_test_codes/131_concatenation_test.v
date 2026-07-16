module concatenation_test (
    input  wire [3:0] a,
    input  wire [3:0] b,
    input  wire [7:0] c,
    output wire [15:0] concat_result
);
    assign concat_result = {c, a, b};
endmodule
