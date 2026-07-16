module parameterized_mux #(
    parameter WIDTH     = 8,
    parameter NUM_INPUTS = 4
) (
    input  wire [NUM_INPUTS-1:0][WIDTH-1:0] data_in,
    input  wire [$clog2(NUM_INPUTS)-1:0]    sel,
    output wire [WIDTH-1:0]                 data_out
);
    assign data_out = data_in[sel];
endmodule
