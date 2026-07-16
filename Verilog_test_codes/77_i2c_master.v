module i2c_master #(
    parameter CLK_DIV = 250
) (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        start,
    input  wire [6:0]  slave_addr,
    input  wire        rw,
    input  wire [7:0]  data_in,
    output reg  [7:0]  data_out,
    output reg         busy,
    output reg         done,
    output reg         ack_err,
    inout  wire        sda,
    output reg         scl
);
    localparam IDLE       = 4'd0;
    localparam START      = 4'd1;
    localparam SEND_ADDR  = 4'd2;
    localparam WAIT_ACK1  = 4'd3;
    localparam SEND_DATA  = 4'd4;
    localparam WAIT_ACK2  = 4'd5;
    localparam READ_DATA  = 4'd6;
    localparam SEND_NACK  = 4'd7;
    localparam STOP       = 4'd8;

    reg [3:0]  state;
    reg [$clog2(CLK_DIV)-1:0] clk_cnt;
    reg [3:0]  bit_cnt;
    reg [7:0]  shift_reg;
    reg        sda_out;
    reg        sda_oe;

    assign sda = sda_oe ? sda_out : 1'bz;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state     <= IDLE;
            busy      <= 1'b0;
            done      <= 1'b0;
            ack_err   <= 1'b0;
            scl       <= 1'b1;
            sda_out   <= 1'b1;
            sda_oe    <= 1'b1;
            clk_cnt   <= {$clog2(CLK_DIV){1'b0}};
            bit_cnt   <= 4'd0;
            shift_reg <= 8'd0;
            data_out  <= 8'd0;
        end else begin
            done <= 1'b0;
            case (state)
                IDLE: begin
                    if (start) begin
                        busy      <= 1'b1;
                        shift_reg <= {slave_addr, rw};
                        state     <= START;
                    end
                end
                START: begin
                    sda_out <= 1'b0;
                    state   <= SEND_ADDR;
                    bit_cnt <= 4'd7;
                end
                SEND_ADDR: begin
                    sda_out <= shift_reg[bit_cnt];
                    if (bit_cnt == 0)
                        state <= WAIT_ACK1;
                    else
                        bit_cnt <= bit_cnt - 1'b1;
                end
                WAIT_ACK1: begin
                    sda_oe <= 1'b0;
                    state  <= rw ? READ_DATA : SEND_DATA;
                    shift_reg <= data_in;
                    bit_cnt <= 4'd7;
                end
                SEND_DATA: begin
                    sda_oe  <= 1'b1;
                    sda_out <= shift_reg[bit_cnt];
                    if (bit_cnt == 0)
                        state <= WAIT_ACK2;
                    else
                        bit_cnt <= bit_cnt - 1'b1;
                end
                WAIT_ACK2: begin
                    sda_oe <= 1'b0;
                    state  <= STOP;
                end
                READ_DATA: begin
                    sda_oe <= 1'b0;
                    if (bit_cnt == 0) begin
                        data_out <= shift_reg;
                        state    <= SEND_NACK;
                    end else begin
                        bit_cnt <= bit_cnt - 1'b1;
                    end
                end
                SEND_NACK: begin
                    sda_oe  <= 1'b1;
                    sda_out <= 1'b1;
                    state   <= STOP;
                end
                STOP: begin
                    sda_out <= 1'b1;
                    busy    <= 1'b0;
                    done    <= 1'b1;
                    state   <= IDLE;
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
