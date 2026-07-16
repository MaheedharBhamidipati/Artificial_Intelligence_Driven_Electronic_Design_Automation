module async_read_ram #(
    parameter ADDR_WIDTH = 8,
    parameter DATA_WIDTH = 8
) (
    input  wire                   clk,
    input  wire                   we,
    input  wire [ADDR_WIDTH-1:0]  addr,
    input  wire [DATA_WIDTH-1:0]  din,
    output wire [DATA_WIDTH-1:0]  dout
);
    reg [DATA_WIDTH-1:0] mem [0:(1<<ADDR_WIDTH)-1];

    always @(posedge clk) begin
        if (we)
            mem[addr] <= din;
    end

    assign dout = mem[addr];
endmodule
