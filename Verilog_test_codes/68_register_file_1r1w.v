module register_file_1r1w #(
    parameter ADDR_WIDTH = 4,
    parameter DATA_WIDTH = 8
) (
    input  wire                   clk,
    input  wire                   rst_n,
    input  wire                   we,
    input  wire [ADDR_WIDTH-1:0]  waddr,
    input  wire [DATA_WIDTH-1:0]  wdata,
    input  wire [ADDR_WIDTH-1:0]  raddr,
    output wire [DATA_WIDTH-1:0]  rdata
);
    reg [DATA_WIDTH-1:0] regs [0:(1<<ADDR_WIDTH)-1];
    integer i;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < (1<<ADDR_WIDTH); i = i + 1)
                regs[i] <= {DATA_WIDTH{1'b0}};
        end else if (we) begin
            regs[waddr] <= wdata;
        end
    end

    assign rdata = regs[raddr];
endmodule
