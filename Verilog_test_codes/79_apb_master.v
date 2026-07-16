module apb_master #(
    parameter ADDR_WIDTH = 8,
    parameter DATA_WIDTH = 32
) (
    input  wire                   pclk,
    input  wire                   presetn,
    input  wire                   start,
    input  wire                   write_en,
    input  wire [ADDR_WIDTH-1:0]  addr_in,
    input  wire [DATA_WIDTH-1:0]  wdata_in,
    output reg  [DATA_WIDTH-1:0]  paddr,
    output reg                    psel,
    output reg                    penable,
    output reg                    pwrite,
    output reg  [DATA_WIDTH-1:0]  pwdata,
    input  wire [DATA_WIDTH-1:0]  prdata,
    input  wire                   pready,
    output reg  [DATA_WIDTH-1:0]  rdata_out,
    output reg                    done
);
    localparam IDLE   = 2'd0;
    localparam SETUP  = 2'd1;
    localparam ACCESS = 2'd2;

    reg [1:0] state;

    always @(posedge pclk or negedge presetn) begin
        if (!presetn) begin
            state     <= IDLE;
            psel      <= 1'b0;
            penable   <= 1'b0;
            pwrite    <= 1'b0;
            paddr     <= {DATA_WIDTH{1'b0}};
            pwdata    <= {DATA_WIDTH{1'b0}};
            done      <= 1'b0;
            rdata_out <= {DATA_WIDTH{1'b0}};
        end else begin
            done <= 1'b0;
            case (state)
                IDLE: begin
                    if (start) begin
                        psel    <= 1'b1;
                        penable <= 1'b0;
                        pwrite  <= write_en;
                        paddr   <= addr_in;
                        pwdata  <= wdata_in;
                        state   <= SETUP;
                    end
                end
                SETUP: begin
                    penable <= 1'b1;
                    state   <= ACCESS;
                end
                ACCESS: begin
                    if (pready) begin
                        rdata_out <= prdata;
                        psel      <= 1'b0;
                        penable   <= 1'b0;
                        done      <= 1'b1;
                        state     <= IDLE;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
