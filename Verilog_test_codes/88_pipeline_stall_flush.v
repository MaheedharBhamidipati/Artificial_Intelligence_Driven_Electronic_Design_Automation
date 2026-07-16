module pipeline_stall_flush #(
    parameter WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             stall,
    input  wire             flush,
    input  wire [WIDTH-1:0] data_in,
    output reg  [WIDTH-1:0] data_out,
    output reg              valid_out
);
    reg [WIDTH-1:0] stage1_data, stage2_data;
    reg             stage1_valid, stage2_valid;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stage1_data  <= {WIDTH{1'b0}};
            stage1_valid <= 1'b0;
        end else if (flush) begin
            stage1_valid <= 1'b0;
        end else if (!stall) begin
            stage1_data  <= data_in;
            stage1_valid <= 1'b1;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stage2_data  <= {WIDTH{1'b0}};
            stage2_valid <= 1'b0;
        end else if (flush) begin
            stage2_valid <= 1'b0;
        end else if (!stall) begin
            stage2_data  <= stage1_data;
            stage2_valid <= stage1_valid;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out  <= {WIDTH{1'b0}};
            valid_out <= 1'b0;
        end else if (flush) begin
            valid_out <= 1'b0;
        end else if (!stall) begin
            data_out  <= stage2_data;
            valid_out <= stage2_valid;
        end
    end
endmodule
