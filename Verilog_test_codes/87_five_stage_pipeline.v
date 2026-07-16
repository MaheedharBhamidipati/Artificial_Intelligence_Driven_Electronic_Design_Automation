module five_stage_pipeline #(
    parameter WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire [WIDTH-1:0] data_in,
    output reg  [WIDTH-1:0] data_out
);
    reg [WIDTH-1:0] stage1, stage2, stage3, stage4;

    // Stage 1: Fetch (pass-through)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) stage1 <= {WIDTH{1'b0}};
        else        stage1 <= data_in;
    end

    // Stage 2: Decode (invert)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) stage2 <= {WIDTH{1'b0}};
        else        stage2 <= ~stage1;
    end

    // Stage 3: Execute (add constant)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) stage3 <= {WIDTH{1'b0}};
        else        stage3 <= stage2 + 1'b1;
    end

    // Stage 4: Memory (shift)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) stage4 <= {WIDTH{1'b0}};
        else        stage4 <= stage3 << 1;
    end

    // Stage 5: Writeback
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) data_out <= {WIDTH{1'b0}};
        else        data_out <= stage4;
    end
endmodule
