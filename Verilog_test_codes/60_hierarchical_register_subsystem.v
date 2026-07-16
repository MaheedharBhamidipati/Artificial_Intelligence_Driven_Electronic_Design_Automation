module register_bank_4 #(
    parameter WIDTH = 8
) (
    input  wire                     clk,
    input  wire                     rst_n,
    input  wire [3:0]               wr_en,
    input  wire [3:0][WIDTH-1:0]    din,
    output wire [3:0][WIDTH-1:0]    dout
);
    genvar i;
    generate
        for (i = 0; i < 4; i = i + 1) begin : rgen
            reg [WIDTH-1:0] r;
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    r <= {WIDTH{1'b0}};
                else if (wr_en[i])
                    r <= din[i];
            end
            assign dout[i] = r;
        end
    endgenerate
endmodule

module hierarchical_register_subsystem #(
    parameter WIDTH = 8
) (
    input  wire                     clk,
    input  wire                     rst_n,
    input  wire [7:0]                wr_en,
    input  wire [7:0][WIDTH-1:0]     din,
    output wire [7:0][WIDTH-1:0]     dout
);
    register_bank_4 #(.WIDTH(WIDTH)) bank0 (
        .clk(clk), .rst_n(rst_n),
        .wr_en(wr_en[3:0]), .din(din[3:0]), .dout(dout[3:0])
    );

    register_bank_4 #(.WIDTH(WIDTH)) bank1 (
        .clk(clk), .rst_n(rst_n),
        .wr_en(wr_en[7:4]), .din(din[7:4]), .dout(dout[7:4])
    );
endmodule
