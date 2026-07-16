module divider #(
    parameter WIDTH = 8
) (
    input  wire                   clk,
    input  wire                   rst_n,
    input  wire                   start,
    input  wire [WIDTH-1:0]       dividend,
    input  wire [WIDTH-1:0]       divisor,
    output reg  [WIDTH-1:0]       quotient,
    output reg  [WIDTH-1:0]       remainder,
    output reg                    done
);
    reg [2*WIDTH-1:0]     rem_reg;
    reg [WIDTH-1:0]       div_reg;
    reg [WIDTH-1:0]       quo_reg;
    reg [$clog2(WIDTH):0] count;
    reg                   running;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rem_reg   <= {2*WIDTH{1'b0}};
            div_reg   <= {WIDTH{1'b0}};
            quo_reg   <= {WIDTH{1'b0}};
            count     <= {($clog2(WIDTH)+1){1'b0}};
            running   <= 1'b0;
            done      <= 1'b0;
            quotient  <= {WIDTH{1'b0}};
            remainder <= {WIDTH{1'b0}};
        end else begin
            if (start && !running) begin
                rem_reg <= {{WIDTH{1'b0}}, dividend};
                div_reg <= divisor;
                quo_reg <= {WIDTH{1'b0}};
                count   <= WIDTH[$clog2(WIDTH):0];
                running <= 1'b1;
                done    <= 1'b0;
            end else if (running) begin
                rem_reg <= rem_reg << 1;
                if (rem_reg[2*WIDTH-2 -: WIDTH] >= div_reg) begin
                    rem_reg[2*WIDTH-2 -: WIDTH] <= rem_reg[2*WIDTH-2 -: WIDTH] - div_reg;
                    quo_reg <= {quo_reg[WIDTH-2:0], 1'b1};
                end else begin
                    quo_reg <= {quo_reg[WIDTH-2:0], 1'b0};
                end
                count <= count - 1'b1;
                if (count == {{($clog2(WIDTH)){1'b0}}, 1'b1}) begin
                    running   <= 1'b0;
                    done      <= 1'b1;
                    quotient  <= quo_reg;
                    remainder <= rem_reg[2*WIDTH-1 -: WIDTH];
                end
            end else begin
                done <= 1'b0;
            end
        end
    end
endmodule
