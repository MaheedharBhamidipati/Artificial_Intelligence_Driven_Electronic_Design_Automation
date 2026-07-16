module parity_checker #(
    parameter WIDTH = 8
)(
    input  wire [WIDTH-1:0] data,
    input  wire parity_bit,

    output wire parity_ok,
    output wire parity_error
);

wire calculated_parity;

assign calculated_parity = ^data;

assign parity_ok    = ~(calculated_parity ^ parity_bit);
assign parity_error =  (calculated_parity ^ parity_bit);

endmodule