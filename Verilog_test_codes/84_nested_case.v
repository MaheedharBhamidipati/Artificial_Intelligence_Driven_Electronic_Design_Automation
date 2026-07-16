module nested_case (
    input  wire [1:0] outer_sel,
    input  wire [1:0] inner_sel,
    input  wire [7:0] a,
    input  wire [7:0] b,
    input  wire [7:0] c,
    input  wire [7:0] d,
    output reg  [7:0] result
);
    always @(*) begin
        result = 8'd0;
        case (outer_sel)
            2'b00: begin
                case (inner_sel)
                    2'b00: result = a;
                    2'b01: result = b;
                    default: result = 8'd0;
                endcase
            end
            2'b01: begin
                case (inner_sel)
                    2'b00: result = c;
                    2'b01: result = d;
                    default: result = 8'd0;
                endcase
            end
            2'b10: begin
                case (inner_sel)
                    2'b00: result = a & b;
                    2'b01: result = c | d;
                    default: result = 8'd0;
                endcase
            end
            default: result = 8'd0;
        endcase
    end
endmodule
