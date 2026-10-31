`timescale 1ns/1ps
module tb_classifier_top;
 reg clk=0;always #5 clk=~clk;reg rstn=0,valid=0,ready=0;
 wire ir,ov,last,err,sat;wire [31:0] d;wire [3:0] k;integer sent=0;
 herb_classifier_top dut(clk,rstn,32'd1000,4'hf,valid,ir,sent==287,d,k,ov,ready,last,err,sat);
 initial begin
  repeat(3) @(negedge clk);rstn=1;valid=1;
  wait(sent==288);@(negedge clk);valid=0;
  wait(ov);repeat(5) begin @(negedge clk);if(d!==0 || !ov || !last || err || sat) $fatal(1,"classifier integration");end
  ready=1;@(negedge clk);$display("PASS all-PL integration with explicitly untrained zero ROM");$finish;
 end
 always @(posedge clk) if(rstn && valid && ir) sent<=sent+1;
 initial begin #100000;$fatal(1,"timeout");end
endmodule
