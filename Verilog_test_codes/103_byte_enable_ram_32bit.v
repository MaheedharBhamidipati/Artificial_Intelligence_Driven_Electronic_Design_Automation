module byte_enable_ram_32bit #(
    parameter ADDR_WIDTH = 8
) (
    input  wire                   clk,
    input  wire [3:0]             byte_en,
    input  wire [ADDR_WIDTH-1:0]  addr,
    input  wire [31:0]            din,
    output reg  [31:0]            dout
);
    reg [7:0] mem_b0 [0:(1<<ADDR_WIDTH)-1];
    reg [7:0] mem_b1 [0:(1<<ADDR_WIDTH)-1];
    reg [7:0] mem_b2 [0:(1<<ADDR_WIDTH)-1];
    reg [7:0] mem_b3 [0:(1<<ADDR_WIDTH)-1];

    always @(posedge clk) begin
        if (byte_en[0]) mem_b0[addr] <= din[7:0];
        if (byte_en[1]) mem_b1[addr] <= din[15:8];
        if (byte_en[2]) mem_b2[addr] <= din[23:16];
        if (byte_en[3]) mem_b3[addr] <= din[31:24];

        dout <= {mem_b3[addr], mem_b2[addr], mem_b1[addr], mem_b0[addr]};
    end
endmodule
