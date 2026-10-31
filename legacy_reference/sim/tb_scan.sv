`timescale 1ns/1ps
module tb_scan;
 reg clk=0;always #5 clk=~clk;reg rstn=0,trigger=0;
 wire s,m,cs,busy,fv,ov;wire [95:0] data;
 localparam [95:0] COMMANDS=96'h0006_0005_0004_0003_0002_0001;
 spi_scan_frontend #(.HALF_PERIOD(2)) dut(clk,rstn,trigger,COMMANDS,m,s,m,cs,busy,fv,data,ov);
 initial begin
  repeat(3) @(negedge clk);rstn=1;trigger=1;@(negedge clk);trigger=0;
  wait(fv);#1;if(data!==COMMANDS || busy || ov) $fatal(1,"scan mismatch");
  $display("PASS six channel SPI scan loopback");$finish;
 end
 initial begin #100000;$fatal(1,"timeout");end
endmodule
