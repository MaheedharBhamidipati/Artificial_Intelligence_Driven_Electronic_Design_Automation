module multi_port_register_file #(
    parameter ADDR_WIDTH = 4,
    parameter DATA_WIDTH = 8,
    parameter NUM_RD_PORTS = 3,
    parameter NUM_WR_PORTS = 2
) (
    input  wire                                          clk,
    input  wire                                          rst_n,
    input  wire [NUM_WR_PORTS-1:0]                       we,
    input  wire [NUM_WR_PORTS-1:0][ADDR_WIDTH-1:0]       waddr,
    input  wire [NUM_WR_PORTS-1:0][DATA_WIDTH-1:0]       wdata,
    input  wire [NUM_RD_PORTS-1:0][ADDR_WIDTH-1:0]       raddr,
    output wire [NUM_RD_PORTS-1:0][DATA_WIDTH-1:0]       rdata
);
    reg [DATA_WIDTH-1:0] regs [0:(1<<ADDR_WIDTH)-1];
    integer i, w;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < (1<<ADDR_WIDTH); i = i + 1)
                regs[i] <= {DATA_WIDTH{1'b0}};
        end else begin
            for (w = 0; w < NUM_WR_PORTS; w = w + 1) begin
                if (we[w])
                    regs[waddr[w]] <= wdata[w];
            end
        end
    end

    genvar r;
    generate
        for (r = 0; r < NUM_RD_PORTS; r = r + 1) begin : rd_gen
            assign rdata[r] = regs[raddr[r]];
        end
    endgenerate
endmodule
