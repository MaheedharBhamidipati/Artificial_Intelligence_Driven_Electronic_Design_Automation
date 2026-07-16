module sync_rom #(
    parameter ADDR_WIDTH = 4,
    parameter DATA_WIDTH = 8
) (
    input  wire                  clk,
    input  wire [ADDR_WIDTH-1:0] addr,
    output reg  [DATA_WIDTH-1:0] dout
);
    reg [DATA_WIDTH-1:0] rom [0:(1<<ADDR_WIDTH)-1];

    initial begin
        rom[0]  = 8'h00; rom[1]  = 8'h01; rom[2]  = 8'h02; rom[3]  = 8'h03;
        rom[4]  = 8'h04; rom[5]  = 8'h05; rom[6]  = 8'h06; rom[7]  = 8'h07;
        rom[8]  = 8'h08; rom[9]  = 8'h09; rom[10] = 8'h0A; rom[11] = 8'h0B;
        rom[12] = 8'h0C; rom[13] = 8'h0D; rom[14] = 8'h0E; rom[15] = 8'h0F;
    end

    always @(posedge clk) begin
        dout <= rom[addr];
    end
endmodule
