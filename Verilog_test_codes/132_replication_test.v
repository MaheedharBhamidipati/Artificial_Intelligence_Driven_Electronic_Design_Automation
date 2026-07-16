module replication_test (
    input  wire [1:0] pattern,
    output wire [7:0] replicated_out,
    output wire [11:0] mixed_replication
);
    assign replicated_out    = {4{pattern}};
    assign mixed_replication = {3{pattern}, {2{2'b01}}};
endmodule
