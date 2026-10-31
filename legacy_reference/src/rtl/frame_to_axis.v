`timescale 1ns/1ps
// Atomic parallel capture boundary. Samples must already be in clk domain.
// A source that cannot pause must monitor sticky overflow; no silent overwrites.
module frame_to_axis #(parameter CHANNELS=6)(
 input wire clk,rstn,frame_valid,input wire [CHANNELS*16-1:0] frame_data,
 input wire frame_last,output wire frame_ready,output reg overflow,
 output wire [31:0] m_axis_tdata,output wire [3:0] m_axis_tkeep,
 output wire m_axis_tvalid,input wire m_axis_tready,output wire m_axis_tlast);
 reg [CHANNELS*16-1:0] hold;reg active,last_hold;integer ch;
 assign frame_ready=!active;
 assign m_axis_tvalid=active;
 assign m_axis_tdata={16'b0,hold[ch*16+:16]};
 assign m_axis_tkeep=4'hf;
 assign m_axis_tlast=active && last_hold && ch==CHANNELS-1;
 always @(posedge clk) begin
  if(!rstn) begin hold<=0;active<=0;last_hold<=0;ch<=0;overflow<=0;end
  else begin
   if(frame_valid) begin
    if(frame_ready) begin hold<=frame_data;active<=1;ch<=0;last_hold<=frame_last;end
    else overflow<=1;
   end
   if(m_axis_tvalid && m_axis_tready)
    if(ch==CHANNELS-1) begin active<=0;ch<=0;end else ch<=ch+1;
  end
 end
endmodule
