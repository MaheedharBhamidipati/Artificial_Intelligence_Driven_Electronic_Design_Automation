module parity_generator_4bit (
    input  wire [3:0] data,
    output wire        parity_bit // even parity
);
    assign parity_bit = ^data;
endmodule
