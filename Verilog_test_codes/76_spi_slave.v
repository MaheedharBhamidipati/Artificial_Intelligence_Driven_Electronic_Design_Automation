module spi_slave #(
    parameter DATA_WIDTH = 8
) (
    input  wire                   sclk,
    input  wire                   rst_n,
    input  wire                   cs_n,
    input  wire                   mosi,
    output reg                    miso,
    input  wire [DATA_WIDTH-1:0]  tx_data,
    output reg  [DATA_WIDTH-1:0]  rx_data,
    output reg                    rx_valid
);
    reg [DATA_WIDTH-1:0]          shift_reg;
    reg [$clog2(DATA_WIDTH)-1:0]  bit_cnt;

    always @(posedge sclk or negedge rst_n) begin
        if (!rst_n) begin
            shift_reg <= {DATA_WIDTH{1'b0}};
            bit_cnt   <= {$clog2(DATA_WIDTH){1'b0}};
            rx_valid  <= 1'b0;
            rx_data   <= {DATA_WIDTH{1'b0}};
        end else if (!cs_n) begin
            shift_reg <= {shift_reg[DATA_WIDTH-2:0], mosi};
            rx_valid  <= 1'b0;
            if (bit_cnt == DATA_WIDTH-1) begin
                bit_cnt  <= {$clog2(DATA_WIDTH){1'b0}};
                rx_valid <= 1'b1;
                rx_data  <= {shift_reg[DATA_WIDTH-2:0], mosi};
            end else begin
                bit_cnt <= bit_cnt + 1'b1;
            end
        end
    end

    always @(negedge sclk or negedge rst_n) begin
        if (!rst_n)
            miso <= 1'b0;
        else if (!cs_n)
            miso <= tx_data[DATA_WIDTH-1-bit_cnt];
    end
endmodule
