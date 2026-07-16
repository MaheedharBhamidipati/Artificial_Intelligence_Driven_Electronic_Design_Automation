module parity_checker_4bit (
    input  wire [3:0] data,
    input  wire        parity_bit,
    output wire        error
);
    assign error = (^data) ^ parity_bit;
endmodule
