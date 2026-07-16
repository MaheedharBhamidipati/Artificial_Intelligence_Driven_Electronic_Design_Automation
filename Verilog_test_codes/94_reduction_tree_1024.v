module reduction_tree_1024 (
    input  wire [1023:0] data_in,
    output wire           and_reduce,
    output wire           or_reduce,
    output wire           xor_reduce
);
    assign and_reduce = &data_in;
    assign or_reduce  = |data_in;
    assign xor_reduce = ^data_in;
endmodule
