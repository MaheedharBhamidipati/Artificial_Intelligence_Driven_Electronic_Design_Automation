module concat_replicate_reduce (
    input  wire [3:0] a,
    input  wire [3:0] b,
    output wire [7:0] concat_result,
    output wire [11:0] replicate_result,
    output wire        and_reduce,
    output wire        or_reduce,
    output wire        xor_reduce
);
    assign concat_result    = {a, b};
    assign replicate_result = {3{a}};
    assign and_reduce       = &a;
    assign or_reduce        = |a;
    assign xor_reduce       = ^a;
endmodule
