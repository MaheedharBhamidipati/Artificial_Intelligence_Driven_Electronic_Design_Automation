// -----------------------------------------------------------------------
// sync_fifo.v -- Parameterized synchronous FIFO (example DUT)
// -----------------------------------------------------------------------
module sync_fifo #(
    parameter WIDTH = 8,
    parameter DEPTH = 16                 // must be a power of 2
) (
    input  wire             clk,
    input  wire             rst_n,       // active-low async reset

    input  wire              wr_en,
    input  wire [WIDTH-1:0]  wr_data,
    output wire               full,

    input  wire              rd_en,
    output reg  [WIDTH-1:0]  rd_data,
    output wire               empty,

    output reg  [$clog2(DEPTH):0] count   // occupancy, 0..DEPTH
);

    localparam AW = $clog2(DEPTH);

    reg [WIDTH-1:0] mem [0:DEPTH-1];
    reg [AW-1:0]    wr_ptr, rd_ptr;

    wire wr_fire = wr_en && !full;
    wire rd_fire = rd_en && !empty;

    assign full  = (count == DEPTH);
    assign empty = (count == 0);

    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr  <= 0;
            rd_ptr  <= 0;
            count   <= 0;
            rd_data <= 0;
            for (i = 0; i < DEPTH; i = i + 1) mem[i] <= 0;
        end else begin
            if (wr_fire) begin
                mem[wr_ptr] <= wr_data;
                wr_ptr      <= wr_ptr + 1'b1;
            end
            if (rd_fire) begin
                rd_data <= mem[rd_ptr];
                rd_ptr  <= rd_ptr + 1'b1;
            end
            case ({wr_fire, rd_fire})
                2'b10:   count <= count + 1'b1;
                2'b01:   count <= count - 1'b1;
                default: count <= count; // 00 or 11: unchanged
            endcase
        end
    end

    // ---------------- Design intent assertions (SVA-lite, plain Verilog) ---
    // These fire only in simulation; synthesis tools ignore $error/initial-less
    // procedural checks like this only if wrapped correctly, so guard with
    // `ifndef SYNTHESIS.
    `ifndef SYNTHESIS
    always @(posedge clk) begin
        if (rst_n) begin
            if (wr_en && full && !rd_en)
                $display("[%0t] ASSERT WARN: write attempted while full and no concurrent read", $time);
            if (rd_en && empty)
                $display("[%0t] ASSERT WARN: read attempted while empty", $time);
            if (count > DEPTH)
                $error("[%0t] ASSERT FAIL: count (%0d) exceeds DEPTH (%0d)", $time, count, DEPTH);
        end
    end
    `endif

endmodule
