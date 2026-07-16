module spi_master #(
    parameter DATA_WIDTH = 8,
    parameter CLK_DIV    = 4
) (
    input  wire                   clk,
    input  wire                   rst_n,
    input  wire                   start,
    input  wire [DATA_WIDTH-1:0]  tx_data,
    output reg  [DATA_WIDTH-1:0]  rx_data,
    output reg                    busy,
    output reg                    done,
    output reg                    sclk,
    output reg                    mosi,
    input  wire                   miso,
    output reg                    cs_n
);
    reg [$clog2(CLK_DIV)-1:0] clk_cnt;
    reg [$clog2(DATA_WIDTH)-1:0] bit_cnt;
    reg [DATA_WIDTH-1:0]       shift_reg;
    reg                        sclk_en;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            busy      <= 1'b0;
            done      <= 1'b0;
            sclk      <= 1'b0;
            mosi      <= 1'b0;
            cs_n      <= 1'b1;
            clk_cnt   <= {$clog2(CLK_DIV){1'b0}};
            bit_cnt   <= {$clog2(DATA_WIDTH){1'b0}};
            shift_reg <= {DATA_WIDTH{1'b0}};
            rx_data   <= {DATA_WIDTH{1'b0}};
        end else begin
            done <= 1'b0;
            if (start && !busy) begin
                busy      <= 1'b1;
                cs_n      <= 1'b0;
                shift_reg <= tx_data;
                bit_cnt   <= DATA_WIDTH[$clog2(DATA_WIDTH)-1:0] - 1'b1;
                clk_cnt   <= {$clog2(CLK_DIV){1'b0}};
                mosi      <= tx_data[DATA_WIDTH-1];
            end else if (busy) begin
                if (clk_cnt == CLK_DIV-1) begin
                    clk_cnt <= {$clog2(CLK_DIV){1'b0}};
                    sclk    <= ~sclk;
                    if (sclk) begin
                        shift_reg <= {shift_reg[DATA_WIDTH-2:0], miso};
                        if (bit_cnt == 0) begin
                            busy    <= 1'b0;
                            done    <= 1'b1;
                            cs_n    <= 1'b1;
                            rx_data <= {shift_reg[DATA_WIDTH-2:0], miso};
                        end else begin
                            bit_cnt <= bit_cnt - 1'b1;
                            mosi    <= shift_reg[DATA_WIDTH-2];
                        end
                    end
                end else begin
                    clk_cnt <= clk_cnt + 1'b1;
                end
            end
        end
    end
endmodule
