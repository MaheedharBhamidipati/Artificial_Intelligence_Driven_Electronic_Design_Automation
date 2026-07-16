module uart_receiver_fsm #(
    parameter CLKS_PER_BIT = 434
) (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       rx_serial,
    output reg        rx_dv,
    output reg  [7:0] rx_byte
);
    localparam IDLE       = 3'd0;
    localparam START_BIT  = 3'd1;
    localparam DATA_BITS  = 3'd2;
    localparam STOP_BIT   = 3'd3;
    localparam CLEANUP    = 3'd4;

    reg [2:0]  state;
    reg [15:0] clk_count;
    reg [2:0]  bit_index;
    reg [7:0]  rx_shift;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state     <= IDLE;
            clk_count <= 16'd0;
            bit_index <= 3'd0;
            rx_dv     <= 1'b0;
            rx_byte   <= 8'd0;
            rx_shift  <= 8'd0;
        end else begin
            case (state)
                IDLE: begin
                    rx_dv     <= 1'b0;
                    clk_count <= 16'd0;
                    bit_index <= 3'd0;
                    if (rx_serial == 1'b0)
                        state <= START_BIT;
                    else
                        state <= IDLE;
                end

                START_BIT: begin
                    if (clk_count == (CLKS_PER_BIT-1)/2) begin
                        if (rx_serial == 1'b0) begin
                            clk_count <= 16'd0;
                            state     <= DATA_BITS;
                        end else begin
                            state <= IDLE;
                        end
                    end else begin
                        clk_count <= clk_count + 16'd1;
                    end
                end

                DATA_BITS: begin
                    if (clk_count < CLKS_PER_BIT-1) begin
                        clk_count <= clk_count + 16'd1;
                    end else begin
                        clk_count <= 16'd0;
                        rx_shift[bit_index] <= rx_serial;
                        if (bit_index < 7) begin
                            bit_index <= bit_index + 3'd1;
                        end else begin
                            bit_index <= 3'd0;
                            state     <= STOP_BIT;
                        end
                    end
                end

                STOP_BIT: begin
                    if (clk_count < CLKS_PER_BIT-1) begin
                        clk_count <= clk_count + 16'd1;
                    end else begin
                        rx_dv     <= 1'b1;
                        rx_byte   <= rx_shift;
                        clk_count <= 16'd0;
                        state     <= CLEANUP;
                    end
                end

                CLEANUP: begin
                    state <= IDLE;
                    rx_dv <= 1'b0;
                end

                default: state <= IDLE;
            endcase
        end
    end
endmodule
