module generate_if_configurable #(
    parameter WIDTH    = 8,
    parameter USE_ADD  = 1  // 1: adder, 0: subtractor
) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output wire [WIDTH-1:0] result
);
    generate
        if (USE_ADD) begin : add_gen
            assign result = a + b;
        end else begin : sub_gen
            assign result = a - b;
        end
    endgenerate
endmodule
