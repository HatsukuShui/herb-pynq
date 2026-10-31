`timescale 1ns/1ps
module tb_spi;
 reg clk=0;always #5 clk=~clk;reg rstn=0,start=0;
 wire sclk,mosi,cs,busy,done;wire [15:0] rx;
 spi_mode0_master #(.HALF_PERIOD(3)) dut(clk,rstn,start,16'ha53c,mosi,sclk,mosi,cs,busy,done,rx);
 initial begin
  repeat(3) @(negedge clk);rstn=1;@(negedge clk);start=1;@(negedge clk);start=0;
  wait(done);#1;if(rx!==16'ha53c || !cs || sclk) $fatal(1,"SPI loopback failed");
  $display("PASS spi loopback");$finish;
 end
 initial begin #10000;$fatal(1,"timeout");end
endmodule
