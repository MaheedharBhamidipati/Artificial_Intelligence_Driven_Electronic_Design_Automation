module pipeline_stage #(
    parameter WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] data_in,
    output reg  [WIDTH-1:0] data_out
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            data_out <= {WIDTH{1'b0}};
        else
            data_out <= data_in;
    end
endmodule

module reusable_pipeline #(
    parameter WIDTH  = 8,
    parameter STAGES = 4
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] data_in,
    output wire [WIDTH-1:0] data_out
);
    wire [WIDTH-1:0] stage_data [0:STAGES];
    assign stage_data[0] = data_in;

    genvar i;
    generate
        for (i = 0; i < STAGES; i = i + 1) begin : stage_gen
            pipeline_stage #(.WIDTH(WIDTH)) u_stage (
                .clk(clk), .rst_n(rst_n),
                .data_in(stage_data[i]), .data_out(stage_data[i+1])
            );
        end
    endgenerate

    assign data_out = stage_data[STAGES];
endmodule
