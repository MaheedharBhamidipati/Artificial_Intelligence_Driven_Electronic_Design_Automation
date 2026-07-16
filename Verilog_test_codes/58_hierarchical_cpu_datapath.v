module reg_file_small (
    input  wire        clk,
    input  wire        we,
    input  wire [2:0]  waddr,
    input  wire [7:0]  wdata,
    input  wire [2:0]  raddr1,
    input  wire [2:0]  raddr2,
    output wire [7:0]  rdata1,
    output wire [7:0]  rdata2
);
    reg [7:0] regs [0:7];

    always @(posedge clk) begin
        if (we)
            regs[waddr] <= wdata;
    end

    assign rdata1 = regs[raddr1];
    assign rdata2 = regs[raddr2];
endmodule

module alu_simple (
    input  wire [1:0] op,
    input  wire [7:0] a,
    input  wire [7:0] b,
    output reg  [7:0] result
);
    always @(*) begin
        case (op)
            2'b00: result = a + b;
            2'b01: result = a - b;
            2'b10: result = a & b;
            2'b11: result = a | b;
            default: result = 8'd0;
        endcase
    end
endmodule

module hierarchical_cpu_datapath (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        reg_we,
    input  wire [2:0]  waddr,
    input  wire [2:0]  raddr1,
    input  wire [2:0]  raddr2,
    input  wire [1:0]  alu_op,
    output wire [7:0]  alu_result
);
    wire [7:0] rdata1, rdata2;

    reg_file_small u_regfile (
        .clk(clk), .we(reg_we), .waddr(waddr), .wdata(alu_result),
        .raddr1(raddr1), .raddr2(raddr2), .rdata1(rdata1), .rdata2(rdata2)
    );

    alu_simple u_alu (
        .op(alu_op), .a(rdata1), .b(rdata2), .result(alu_result)
    );
endmodule
