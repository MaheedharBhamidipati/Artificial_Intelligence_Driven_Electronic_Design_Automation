module sync2 #(
    parameter WIDTH = 4
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] din,
    output reg  [WIDTH-1:0] dout
);
    reg [WIDTH-1:0] stage1;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stage1 <= {WIDTH{1'b0}};
            dout   <= {WIDTH{1'b0}};
        end else begin
            stage1 <= din;
            dout   <= stage1;
        end
    end
endmodule

module async_fifo #(
    parameter DATA_WIDTH = 8,
    parameter ADDR_WIDTH = 4
) (
    input  wire                   wr_clk,
    input  wire                   wr_rst_n,
    input  wire                   wr_en,
    input  wire [DATA_WIDTH-1:0]  din,
    output wire                   full,

    input  wire                   rd_clk,
    input  wire                   rd_rst_n,
    input  wire                   rd_en,
    output reg  [DATA_WIDTH-1:0]  dout,
    output wire                   empty
);
    reg  [DATA_WIDTH-1:0] mem [0:(1<<ADDR_WIDTH)-1];

    reg  [ADDR_WIDTH:0] wr_ptr_bin, rd_ptr_bin;
    wire [ADDR_WIDTH:0] wr_ptr_gray, rd_ptr_gray;
    wire [ADDR_WIDTH:0] wr_ptr_gray_sync, rd_ptr_gray_sync;

    assign wr_ptr_gray = wr_ptr_bin ^ (wr_ptr_bin >> 1);
    assign rd_ptr_gray = rd_ptr_bin ^ (rd_ptr_bin >> 1);

    sync2 #(.WIDTH(ADDR_WIDTH+1)) sync_wr2rd (
        .clk(rd_clk), .rst_n(rd_rst_n), .din(wr_ptr_gray), .dout(wr_ptr_gray_sync)
    );

    sync2 #(.WIDTH(ADDR_WIDTH+1)) sync_rd2wr (
        .clk(wr_clk), .rst_n(wr_rst_n), .din(rd_ptr_gray), .dout(rd_ptr_gray_sync)
    );

    always @(posedge wr_clk or negedge wr_rst_n) begin
        if (!wr_rst_n)
            wr_ptr_bin <= {(ADDR_WIDTH+1){1'b0}};
        else if (wr_en && !full) begin
            mem[wr_ptr_bin[ADDR_WIDTH-1:0]] <= din;
            wr_ptr_bin <= wr_ptr_bin + 1'b1;
        end
    end

    assign full = (wr_ptr_gray == {~rd_ptr_gray_sync[ADDR_WIDTH:ADDR_WIDTH-1], rd_ptr_gray_sync[ADDR_WIDTH-2:0]});

    always @(posedge rd_clk or negedge rd_rst_n) begin
        if (!rd_rst_n) begin
            rd_ptr_bin <= {(ADDR_WIDTH+1){1'b0}};
            dout       <= {DATA_WIDTH{1'b0}};
        end else if (rd_en && !empty) begin
            dout       <= mem[rd_ptr_bin[ADDR_WIDTH-1:0]];
            rd_ptr_bin <= rd_ptr_bin + 1'b1;
        end
    end

    assign empty = (rd_ptr_gray == wr_ptr_gray_sync);
endmodule
