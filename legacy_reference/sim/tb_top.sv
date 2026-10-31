`timescale 1ns/1ps
module tb_top;
 reg clk=0;always #4 clk=~clk;reg btn=1;wire [3:0] led;
 top dut(clk,btn,led);
 initial begin repeat(4) @(negedge clk);btn=0;repeat(2000) @(negedge clk);
 if(led[2] || !led[3]) $fatal(1,"top reset or protocol error");
 $display("PASS top smoke");$finish;end
endmodule
