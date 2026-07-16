module cnn_pipelined (

    input clk,

    input rst_n,

    input [23:0] rgb_in,

    output reg health_status

);



    wire [7:0] grayscale;

    wire [7:0] resized;

    wire [15:0] feature_out;

    wire [15:0] pooled_out;



    image_preprocessing ip (

        .clk(clk),

        .rst_n(rst_n),

        .rgb_in(rgb_in),

        .grayscale_out(grayscale),

        .resized_out(resized)

    );



    convolution conv (

        .clk(clk),

        .rst_n(rst_n),

        .pixel_in(resized),

        .feature_out(feature_out)

    );



    max_pooling pool (

        .clk(clk),

        .rst_n(rst_n),

        .feature_in(feature_out),

        .pooled_out(pooled_out)

    );



    classification classify (

        .clk(clk),

        .rst_n(rst_n),

        .pooled_in(pooled_out),

        .health_status(health_status)

    );



endmodule



module image_preprocessing (

    input clk,

    input rst_n,

    input [23:0] rgb_in,

    output reg [7:0] grayscale_out,

    output reg [7:0] resized_out

);



    always @(posedge clk or negedge rst_n) begin

        if (!rst_n) begin

            grayscale_out <= 8'd0;

            resized_out <= 8'd0;

        end

        else begin

            grayscale_out <= 

                (rgb_in[23:16] * 30 + 

                 rgb_in[15:8]  * 59 + 

                 rgb_in[7:0]   * 11) / 100;



            resized_out <= grayscale_out >> 1;

        end

    end



endmodule



module convolution (

    input clk,

    input rst_n,

    input [7:0] pixel_in,

    output reg [15:0] feature_out

);



    always @(posedge clk or negedge rst_n) begin

        if (!rst_n)

            feature_out <= 16'd0;

        else

            feature_out <= (pixel_in * 5) + (pixel_in >> 2) - 15;

    end



endmodule



module max_pooling (

    input clk,

    input rst_n,

    input [15:0] feature_in,

    output reg [15:0] pooled_out

);



    always @(posedge clk or negedge rst_n) begin

        if (!rst_n)

            pooled_out <= 16'd0;

        else

            pooled_out <= (feature_in > 16'd200) ? 16'd200 : feature_in;

    end



endmodule



module classification (

    input clk,

    input rst_n,

    input [15:0] pooled_in,

    output reg health_status

);



    always @(posedge clk or negedge rst_n) begin

        if (!rst_n)

            health_status <= 1'b0;

        else

            health_status <= (pooled_in > 16'd120) ? 1'b1 : 1'b0;

    end



endmodule