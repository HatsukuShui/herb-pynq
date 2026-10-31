`timescale 1ns/1ps
module tb_classifier;
 reg clk=0;always #5 clk=~clk;reg rstn=0;reg signed [15:0] x=0;reg valid=0,ready=0;
 wire fr,rv;wire [7:0] id;
 linear_classifier #(.FEATURES(2),.CLASSES(2)) dut(clk,rstn,x,valid,fr,id,rv,ready);
 initial begin
  #1;dut.weights[0]=1;dut.weights[1]=-1;dut.weights[2]=-1;dut.weights[3]=2;
  repeat(3) @(negedge clk);rstn=1;
  @(negedge clk);x=3;valid=1;@(negedge clk);x=7;@(negedge clk);valid=0;
  wait(rv);#1;if(id!==1) $fatal(1,"classifier argmax");
  repeat(5) begin @(negedge clk);if(!rv || id!==1 || fr) $fatal(1,"classifier hold");end
  ready=1;@(negedge clk);ready=0;
  x=-3;valid=1;@(negedge clk);x=-7;@(negedge clk);valid=0;
  wait(rv);#1;if(id!==0) $fatal(1,"negative classifier");
  $display("PASS classifier signed MAC and result backpressure");$finish;
 end
 initial begin #10000;$fatal(1,"timeout");end
endmodule
