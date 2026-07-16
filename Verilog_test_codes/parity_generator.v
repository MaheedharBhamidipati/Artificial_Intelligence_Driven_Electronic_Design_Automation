module parity_generator #(
    parameter WIDTH = 8
)(
    input  wire [WIDTH-1:0] data,
    output wire even_parity,
    output wire odd_parity
);

assign even_parity = ^data;
assign odd_parity  = ~(^data);

endmodule