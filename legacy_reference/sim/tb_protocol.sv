`timescale 1ns/1ps
module tb_protocol;
 reg clk=0;always #5 clk=~clk;reg rstn=0,valid=0,last=0;reg [3:0] kin=15;
 wire ready,ov,ol,err;wire [31:0] d;wire [3:0] k;
 herb_axis_core dut(clk,rstn,32'd0,kin,valid,ready,last,d,k,ov,1'b1,ol,err);
 initial begin
  repeat(3) @(negedge clk);rstn=1;valid=1;last=1;
  @(negedge clk);valid=0;if(!err || ready) $fatal(1,"early TLAST not detected");
  rstn=0;@(negedge clk);rstn=1;valid=1;last=0;kin=3;
  @(negedge clk);valid=0;if(!err) $fatal(1,"bad TKEEP not detected");
  rstn=0;@(negedge clk);rstn=1;@(negedge clk);
  if(err || !ready) $fatal(1,"reset recovery");
  $display("PASS malformed packets and reset recovery");$finish;
 end
endmodule
