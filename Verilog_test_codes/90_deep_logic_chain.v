module deep_logic_chain #(
    parameter WIDTH = 8,
    parameter DEPTH = 32
) (
    input  wire [WIDTH-1:0] data_in,
    output wire [WIDTH-1:0] data_out
);
    wire [WIDTH-1:0] chain [0:DEPTH];
    assign chain[0] = data_in;

    genvar i;
    generate
        for (i = 0; i < DEPTH; i = i + 1) begin : chain_gen
            assign chain[i+1] = chain[i] ^ {WIDTH{1'b1}} & (chain[i] + 1'b1);
        end
    endgenerate

    assign data_out = chain[DEPTH];
endmodule
