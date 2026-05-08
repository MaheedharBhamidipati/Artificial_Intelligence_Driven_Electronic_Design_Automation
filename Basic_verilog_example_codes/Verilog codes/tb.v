
`timescale 1ns/1ps

module and_gate_tb;

reg a;
wire y;

and_gate uut (
.a(a),
.y(y)
);

initial begin
    $dumpfile("D:/AI_EDA_TOOL/runs/wave.vcd");
    $dumpvars(0, uut);
    a = 0;

    a = 0;
    #10;

    a = 1;
    #10;


    $finish;
end

endmodule
