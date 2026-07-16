module single_port_rom #(
    parameter ADDR_WIDTH = 4,
    parameter DATA_WIDTH = 8
) (
    input  wire [ADDR_WIDTH-1:0]  addr,
    output wire [DATA_WIDTH-1:0]  dout
);
    reg [DATA_WIDTH-1:0] rom [0:(1<<ADDR_WIDTH)-1];

    initial begin
        rom[0]  = 8'h00; rom[1]  = 8'h11; rom[2]  = 8'h22; rom[3]  = 8'h33;
        rom[4]  = 8'h44; rom[5]  = 8'h55; rom[6]  = 8'h66; rom[7]  = 8'h77;
        rom[8]  = 8'h88; rom[9]  = 8'h99; rom[10] = 8'hAA; rom[11] = 8'hBB;
        rom[12] = 8'hCC; rom[13] = 8'hDD; rom[14] = 8'hEE; rom[15] = 8'hFF;
    end

    assign dout = rom[addr]; // combinational read-only access
endmodule
