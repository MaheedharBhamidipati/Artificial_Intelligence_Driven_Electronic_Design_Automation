module byte_enable_ram #(
    parameter ADDR_WIDTH = 8,
    parameter NUM_BYTES  = 4
) (
    input  wire                          clk,
    input  wire [NUM_BYTES-1:0]          byte_en,
    input  wire [ADDR_WIDTH-1:0]         addr,
    input  wire [NUM_BYTES*8-1:0]        din,
    output reg  [NUM_BYTES*8-1:0]        dout
);
    reg [7:0] mem [0:NUM_BYTES-1][0:(1<<ADDR_WIDTH)-1];
    integer i;

    always @(posedge clk) begin
        for (i = 0; i < NUM_BYTES; i = i + 1) begin
            if (byte_en[i])
                mem[i][addr] <= din[i*8 +: 8];
            dout[i*8 +: 8] <= mem[i][addr];
        end
    end
endmodule
