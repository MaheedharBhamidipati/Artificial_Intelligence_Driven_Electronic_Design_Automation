module large_register_bank_1024 #(
    parameter WIDTH = 8
) (
    input  wire                    clk,
    input  wire                    rst_n,
    input  wire                    wr_en,
    input  wire [9:0]               addr,
    input  wire [WIDTH-1:0]         din,
    output wire [WIDTH-1:0]         dout
);
    reg [WIDTH-1:0] regs [0:1023];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset handled per-access to keep synthesis efficient;
            // large register banks typically rely on power-on init or
            // a scan-based reset rather than a full parallel reset.
            regs[addr] <= {WIDTH{1'b0}};
        end else if (wr_en) begin
            regs[addr] <= din;
        end
    end

    assign dout = regs[addr];
endmodule
