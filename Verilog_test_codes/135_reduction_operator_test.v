module reduction_operator_test #(
    parameter WIDTH = 8
) (
    input  wire [WIDTH-1:0] data_in,
    output wire             and_reduce,
    output wire             nand_reduce,
    output wire             or_reduce,
    output wire             nor_reduce,
    output wire             xor_reduce,
    output wire             xnor_reduce
);
    assign and_reduce  = &data_in;
    assign nand_reduce = ~&data_in;
    assign or_reduce   = |data_in;
    assign nor_reduce  = ~|data_in;
    assign xor_reduce  = ^data_in;
    assign xnor_reduce = ~^data_in;
endmodule
