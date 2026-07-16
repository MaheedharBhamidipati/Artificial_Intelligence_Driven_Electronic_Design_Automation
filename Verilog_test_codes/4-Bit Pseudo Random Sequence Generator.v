module lfsr_4bit (
    input clk,
    input rst,
    output reg [3:0] lfsr
);

wire feedback;

assign feedback = lfsr[3] ^ lfsr[2];

always @(posedge clk or posedge rst)
begin

    if(rst)
        lfsr <= 4'b0001;

    else
        lfsr <= {lfsr[2:0], feedback};

end

endmodule