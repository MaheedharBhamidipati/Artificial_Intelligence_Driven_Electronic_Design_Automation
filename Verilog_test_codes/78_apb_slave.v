module apb_slave #(
    parameter ADDR_WIDTH = 8,
    parameter DATA_WIDTH = 32
) (
    input  wire                   pclk,
    input  wire                   presetn,
    input  wire [ADDR_WIDTH-1:0]  paddr,
    input  wire                   psel,
    input  wire                   penable,
    input  wire                   pwrite,
    input  wire [DATA_WIDTH-1:0]  pwdata,
    output reg  [DATA_WIDTH-1:0]  prdata,
    output reg                    pready,
    output reg                    pslverr
);
    reg [DATA_WIDTH-1:0] mem [0:(1<<ADDR_WIDTH)-1];

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            prdata  <= {DATA_WIDTH{1'b0}};
            pready  <= 1'b0;
            pslverr <= 1'b0;
        end else begin
            pready  <= 1'b0;
            pslverr <= 1'b0;
            if (psel && penable) begin
                pready <= 1'b1;
                if (pwrite)
                    mem[paddr] <= pwdata;
                else
                    prdata <= mem[paddr];
            end
        end
    end
endmodule
