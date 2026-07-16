// Intentional RTL stress case: multiple drivers on the same signal
module multiple_driver (
    input  wire       sel_a,
    input  wire       sel_b,
    input  wire [7:0] data_a,
    input  wire [7:0] data_b,
    output wire [7:0] shared_bus
);
    // Both continuous assignments drive 'shared_bus' -> multiple driver conflict
    assign shared_bus = sel_a ? data_a : 8'bz;
    assign shared_bus = sel_b ? data_b : 8'bz;
endmodule
