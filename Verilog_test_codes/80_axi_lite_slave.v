module axi_lite_slave #(
    parameter ADDR_WIDTH = 8,
    parameter DATA_WIDTH = 32
) (
    input  wire                   aclk,
    input  wire                   aresetn,

    input  wire [ADDR_WIDTH-1:0]  awaddr,
    input  wire                   awvalid,
    output reg                    awready,

    input  wire [DATA_WIDTH-1:0]  wdata,
    input  wire [DATA_WIDTH/8-1:0] wstrb,
    input  wire                   wvalid,
    output reg                    wready,

    output reg  [1:0]             bresp,
    output reg                    bvalid,
    input  wire                   bready,

    input  wire [ADDR_WIDTH-1:0]  araddr,
    input  wire                   arvalid,
    output reg                    arready,

    output reg  [DATA_WIDTH-1:0]  rdata,
    output reg  [1:0]             rresp,
    output reg                    rvalid,
    input  wire                   rready
);
    reg [DATA_WIDTH-1:0] mem [0:(1<<ADDR_WIDTH)-1];
    reg [ADDR_WIDTH-1:0] awaddr_reg, araddr_reg;
    integer i;

    // Write address channel
    always @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            awready    <= 1'b0;
            awaddr_reg <= {ADDR_WIDTH{1'b0}};
        end else begin
            if (!awready && awvalid && wvalid) begin
                awready    <= 1'b1;
                awaddr_reg <= awaddr;
            end else begin
                awready <= 1'b0;
            end
        end
    end

    // Write data channel
    always @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            wready <= 1'b0;
        end else begin
            if (!wready && wvalid && awvalid) begin
                wready <= 1'b1;
                for (i = 0; i < DATA_WIDTH/8; i = i + 1) begin
                    if (wstrb[i])
                        mem[awaddr_reg][i*8 +: 8] <= wdata[i*8 +: 8];
                end
            end else begin
                wready <= 1'b0;
            end
        end
    end

    // Write response channel
    always @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            bvalid <= 1'b0;
            bresp  <= 2'b00;
        end else begin
            if (awready && wready && !bvalid) begin
                bvalid <= 1'b1;
                bresp  <= 2'b00;
            end else if (bvalid && bready) begin
                bvalid <= 1'b0;
            end
        end
    end

    // Read address channel
    always @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            arready    <= 1'b0;
            araddr_reg <= {ADDR_WIDTH{1'b0}};
        end else begin
            if (!arready && arvalid) begin
                arready    <= 1'b1;
                araddr_reg <= araddr;
            end else begin
                arready <= 1'b0;
            end
        end
    end

    // Read data channel
    always @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            rvalid <= 1'b0;
            rresp  <= 2'b00;
            rdata  <= {DATA_WIDTH{1'b0}};
        end else begin
            if (arready && !rvalid) begin
                rvalid <= 1'b1;
                rresp  <= 2'b00;
                rdata  <= mem[araddr_reg];
            end else if (rvalid && rready) begin
                rvalid <= 1'b0;
            end
        end
    end
endmodule
