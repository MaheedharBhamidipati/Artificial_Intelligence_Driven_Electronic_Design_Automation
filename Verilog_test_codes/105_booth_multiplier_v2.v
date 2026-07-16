module booth_multiplier_v2 #(
    parameter WIDTH = 8
) (
    input  wire                       clk,
    input  wire                       rst_n,
    input  wire                       start,
    input  wire signed [WIDTH-1:0]    multiplicand,
    input  wire signed [WIDTH-1:0]    multiplier,
    output reg  signed [2*WIDTH-1:0]  product,
    output reg                        done
);
    reg [2*WIDTH:0]        acc;
    reg [$clog2(WIDTH):0]  count;
    reg                    running;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc     <= {(2*WIDTH+1){1'b0}};
            count   <= {($clog2(WIDTH)+1){1'b0}};
            running <= 1'b0;
            done    <= 1'b0;
            product <= {2*WIDTH{1'b0}};
        end else begin
            if (start && !running) begin
                acc[2*WIDTH:WIDTH+1] <= {WIDTH{1'b0}};
                acc[WIDTH:1]         <= multiplier;
                acc[0]               <= 1'b0;
                count   <= WIDTH[$clog2(WIDTH):0];
                running <= 1'b1;
                done    <= 1'b0;
            end else if (running) begin
                case (acc[1:0])
                    2'b01: acc[2*WIDTH:WIDTH+1] <= acc[2*WIDTH:WIDTH+1] + multiplicand;
                    2'b10: acc[2*WIDTH:WIDTH+1] <= acc[2*WIDTH:WIDTH+1] - multiplicand;
                    default: acc[2*WIDTH:WIDTH+1] <= acc[2*WIDTH:WIDTH+1];
                endcase
                acc <= {acc[2*WIDTH], acc[2*WIDTH:1]};
                count <= count - 1'b1;
                if (count == {{($clog2(WIDTH)){1'b0}}, 1'b1}) begin
                    running <= 1'b0;
                    done    <= 1'b1;
                    product <= acc[2*WIDTH:1];
                end
            end else begin
                done <= 1'b0;
            end
        end
    end
endmodule
