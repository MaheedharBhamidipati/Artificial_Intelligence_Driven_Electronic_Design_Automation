module booth_multiplier #(
    parameter WIDTH = 8
) (
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 start,
    input  wire [WIDTH-1:0]     multiplicand,
    input  wire [WIDTH-1:0]     multiplier,
    output reg  [2*WIDTH-1:0]   product,
    output reg                  done
);
    reg [2*WIDTH:0]   acc_reg;
    reg [WIDTH-1:0]   count;
    reg               running;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            acc_reg <= {(2*WIDTH+1){1'b0}};
            count   <= {WIDTH{1'b0}};
            running <= 1'b0;
            done    <= 1'b0;
            product <= {2*WIDTH{1'b0}};
        end else begin
            if (start && !running) begin
                acc_reg <= {{WIDTH{1'b0}}, multiplier, 1'b0};
                acc_reg[2*WIDTH-1 -: WIDTH] <= {WIDTH{1'b0}};
                acc_reg[WIDTH-1:0] <= {multiplier[WIDTH-1:0]};
                count   <= WIDTH[WIDTH-1:0];
                running <= 1'b1;
                done    <= 1'b0;
            end else if (running) begin
                case (acc_reg[1:0])
                    2'b01: acc_reg[2*WIDTH:WIDTH] <= acc_reg[2*WIDTH:WIDTH] + multiplicand;
                    2'b10: acc_reg[2*WIDTH:WIDTH] <= acc_reg[2*WIDTH:WIDTH] - multiplicand;
                    default: acc_reg[2*WIDTH:WIDTH] <= acc_reg[2*WIDTH:WIDTH];
                endcase
                acc_reg <= {acc_reg[2*WIDTH], acc_reg[2*WIDTH:1]};
                count   <= count - 1'b1;
                if (count == {{(WIDTH-1){1'b0}},1'b1}) begin
                    running <= 1'b0;
                    done    <= 1'b1;
                    product <= acc_reg[2*WIDTH-1:0];
                end
            end else begin
                done <= 1'b0;
            end
        end
    end
endmodule
