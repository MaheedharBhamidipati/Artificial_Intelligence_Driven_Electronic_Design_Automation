module dense_interconnect_fabric #(
    parameter NUM_NODES = 8,
    parameter WIDTH     = 8
) (
    input  wire [NUM_NODES-1:0][WIDTH-1:0]                    node_in,
    input  wire [NUM_NODES-1:0][$clog2(NUM_NODES)-1:0]        node_sel,
    output wire [NUM_NODES-1:0][WIDTH-1:0]                    node_out
);
    genvar i;
    generate
        for (i = 0; i < NUM_NODES; i = i + 1) begin : fabric_gen
            assign node_out[i] = node_in[node_sel[i]];
        end
    endgenerate
endmodule
