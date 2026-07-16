module priority_encoder #(
    parameter WIDTH = 8
)(
    input  wire [WIDTH-1:0] din,

    output reg  [$clog2(WIDTH)-1:0] code,
    output reg                      valid
);

integer i;

always @(*) begin

    code  = 0;
    valid = 0;

    for(i=WIDTH-1;i>=0;i=i-1)
    begin
        if(din[i] && !valid)
        begin
            code  = i;
            valid = 1'b1;
        end
    end

end

endmodule