module two_stage_pipeline #(
    parameter WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output reg  [WIDTH-1:0] result
);
    reg [WIDTH-1:0] stage1_sum;
    reg [WIDTH-1:0] stage1_a;

    // Stage 1: add
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stage1_sum <= {WIDTH{1'b0}};
            stage1_a   <= {WIDTH{1'b0}};
        end else begin
            stage1_sum <= a + b;
            stage1_a   <= a;
        end
    end

    // Stage 2: use result of stage1
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            result <= {WIDTH{1'b0}};
        else
            result <= stage1_sum ^ stage1_a;
    end
endmodule
