`timescale 1ns/1ps
module tb_frame;
 reg clk=0;always #5 clk=~clk;reg rstn=0,fv=0,ready=0;
 wire fr,ov,v,last;wire [31:0] d;wire [3:0] k;integer n=0;
 frame_to_axis dut(clk,rstn,fv,{16'd6,16'd5,16'd4,16'd3,16'd2,16'd1},1'b1,fr,ov,d,k,v,ready,last);
 initial begin
  repeat(3) @(negedge clk);rstn=1;fv=1;@(negedge clk);fv=0;
  repeat(4) begin @(negedge clk);if(!v || d!=1 || last) $fatal(1,"frame hold");end
  fv=1;@(negedge clk);fv=0;if(!ov) $fatal(1,"overflow missing");ready=1;
  wait(n==6);@(negedge clk);if(!fr) $fatal(1,"frame not released");
  $display("PASS frame channel order, backpressure, overflow");$finish;
 end
 always @(posedge clk) if(v && ready) begin
  if(d!=n+1 || last!=(n==5)) $fatal(1,"frame order");n=n+1;
 end
 initial begin #10000;$fatal(1,"timeout");end
endmodule
