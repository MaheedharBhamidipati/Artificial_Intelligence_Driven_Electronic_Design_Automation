module simple_dual_port_ram #(
    parameter ADDR_WIDTH = 8,
    parameter DATA_WIDTH = 8
) (
    input  wire                   clk,
    input  wire                   we,
    input  wire [ADDR_WIDTH-1:0]  waddr,
    input  wire [DATA_WIDTH-1:0]  din,
    input  wire [ADDR_WIDTH-1:0]  raddr,
    output reg  [DATA_WIDTH-1:0]  dout
);
    reg [DATA_WIDTH-1:0] mem [0:(1<<ADDR_WIDTH)-1];

    always @(posedge clk) begin
        if (we)
            mem[waddr] <= din;
        dout <= mem[raddr];
    end
endmodule
