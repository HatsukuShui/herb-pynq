`timescale 1ns/1ps
// Standalone board self-test. NO external ADC or trained classifier connected.
// btn0 resets; led0 heartbeat, led1 feature packets, led2 protocol error, led3 reset released.
module top(input wire clk125,input wire btn0,output wire [3:0] led);
 wire rstn;reset_sync u_reset(clk125,btn0,rstn);
 reg [26:0] ticks=0;reg [31:0] index=0;reg calibrated=0;reg result_toggle=0;
 wire ready,valid,last,error;wire [31:0] result;wire [3:0] keep;
 wire [31:0] packet_words=calibrated ? 192 : 288;
 wire [31:0] synthetic=1000+(index%6)*100+((index/6)%32)*2;
 always @(posedge clk125) begin
  if(!rstn) begin ticks<=0;index<=0;calibrated<=0;result_toggle<=0;end
  else begin
   ticks<=ticks+1;
   if(ready) if(index==packet_words-1) begin index<=0;calibrated<=1;end else index<=index+1;
   if(valid && last) result_toggle<=~result_toggle;
  end
 end
 herb_axis_core u_core(.aclk(clk125),.aresetn(rstn),.s_axis_tdata(synthetic),.s_axis_tkeep(4'hf),
 .s_axis_tvalid(1'b1),.s_axis_tready(ready),.s_axis_tlast(index==packet_words-1),
 .m_axis_tdata(result),.m_axis_tkeep(keep),.m_axis_tvalid(valid),.m_axis_tready(1'b1),
 .m_axis_tlast(last),.protocol_error(error));
 assign led={rstn,error,result_toggle,ticks[26]};
endmodule
