module generate_register_bank #(
    parameter WIDTH     = 8,
    parameter NUM_REGS  = 8
) (
    input  wire                          clk,
    input  wire                          rst_n,
    input  wire [NUM_REGS-1:0]           wr_en,
    input  wire [NUM_REGS-1:0][WIDTH-1:0] din,
    output wire [NUM_REGS-1:0][WIDTH-1:0] dout
);
    genvar i;
    generate
        for (i = 0; i < NUM_REGS; i = i + 1) begin : reg_gen
            reg [WIDTH-1:0] reg_data;

            always @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    reg_data <= {WIDTH{1'b0}};
                else if (wr_en[i])
                    reg_data <= din[i];
            end

            assign dout[i] = reg_data;
        end
    endgenerate
endmodule
