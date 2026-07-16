module encoder #(
    parameter INPUT_WIDTH = 8
)(
    input  wire [INPUT_WIDTH-1:0] din,
    output reg  [$clog2(INPUT_WIDTH)-1:0] dout
);

integer i;

always @(*) begin

    dout = 0;

    for(i=0;i<INPUT_WIDTH;i=i+1)
    begin
        if(din[i])
            dout = i;
    end

end

endmodule