`timescale 1ns/1ps
module reset_sync(input wire clk, input wire arst, output wire rstn);
 (* ASYNC_REG="TRUE" *) reg [1:0] sync_ff=0;
 always @(posedge clk or posedge arst)
  if(arst) sync_ff<=0; else sync_ff<={sync_ff[0],1'b1};
 assign rstn=sync_ff[1];
endmodule
