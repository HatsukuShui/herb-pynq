`timescale 1ns/1ps
// Six-channel stream -> baseline removal -> IIR -> window features.
// Input signed 16-bit in low half of each 32-bit AXIS word, channel implicit.
// First BASE_FRAMES frames after reset are clean-air calibration (no output).
// Thereafter each WINDOW_FRAMES frames produce channel-major [mean,max,min,last-first].
module herb_axis_core #(
 parameter CHANNELS=6, BASE_LOG2=4, WINDOW_LOG2=5, FILTER_SHIFT=2
)(input wire aclk, input wire aresetn,
 input wire [31:0] s_axis_tdata, input wire [3:0] s_axis_tkeep,
 input wire s_axis_tvalid, output wire s_axis_tready, input wire s_axis_tlast,
 output wire [31:0] m_axis_tdata, output wire [3:0] m_axis_tkeep,
 output wire m_axis_tvalid, input wire m_axis_tready, output wire m_axis_tlast,
 output reg protocol_error);
 localparam BASE_FRAMES=1<<BASE_LOG2, WINDOW_FRAMES=1<<WINDOW_LOG2;
 reg emitting, calibrated;
 integer ch, frame, out_ch, out_kind, i;
 reg signed [31:0] base_sum[0:CHANNELS-1], baseline[0:CHANNELS-1];
 reg signed [31:0] filt[0:CHANNELS-1], sum[0:CHANNELS-1];
 reg signed [31:0] peak[0:CHANNELS-1], trough[0:CHANNELS-1];
 reg signed [31:0] first[0:CHANNELS-1], last[0:CHANNELS-1];
 wire signed [31:0] sample_ext={{16{s_axis_tdata[15]}},s_axis_tdata[15:0]};
 wire signed [31:0] next_filt=filt[ch]+((sample_ext-baseline[ch]-filt[ch])>>>FILTER_SHIFT);
 assign s_axis_tready=!emitting && !protocol_error && aresetn;
 assign m_axis_tvalid=emitting && aresetn;
 assign m_axis_tkeep=4'hf;
 assign m_axis_tlast=emitting && out_ch==CHANNELS-1 && out_kind==3;
 assign m_axis_tdata=out_kind==0 ? (sum[out_ch]>>>WINDOW_LOG2) :
                         out_kind==1 ? peak[out_ch] :
                         out_kind==2 ? trough[out_ch] : last[out_ch]-first[out_ch];
 always @(posedge aclk) begin
  if(!aresetn) begin
   emitting<=0;calibrated<=0;protocol_error<=0;ch<=0;frame<=0;out_ch<=0;out_kind<=0;
   for(i=0;i<CHANNELS;i=i+1) begin
    base_sum[i]<=0;baseline[i]<=0;filt[i]<=0;sum[i]<=0;
    peak[i]<=0;trough[i]<=0;first[i]<=0;last[i]<=0;
   end
  end else begin
   if(s_axis_tvalid && s_axis_tready) begin
    // TLAST is end of one entire calibration+window or subsequent window packet.
    if(s_axis_tkeep!=4'hf || s_axis_tlast !=
      (ch==CHANNELS-1 && calibrated && frame==WINDOW_FRAMES-1)) protocol_error<=1;
    if(!calibrated) begin
     base_sum[ch]<=base_sum[ch]+sample_ext;
     if(frame==BASE_FRAMES-1) baseline[ch]<=(base_sum[ch]+sample_ext)>>>BASE_LOG2;
    end else begin
     filt[ch]<=next_filt; last[ch]<=next_filt;
     if(frame==0) begin
      first[ch]<=next_filt;sum[ch]<=next_filt;peak[ch]<=next_filt;trough[ch]<=next_filt;
     end else begin
      sum[ch]<=sum[ch]+next_filt;
      if(next_filt>peak[ch]) peak[ch]<=next_filt;
      if(next_filt<trough[ch]) trough[ch]<=next_filt;
     end
    end
    if(ch==CHANNELS-1) begin
     ch<=0;
     if(!calibrated && frame==BASE_FRAMES-1) begin frame<=0;calibrated<=1;end
     else if(calibrated && frame==WINDOW_FRAMES-1) begin
      frame<=0;emitting<=1;out_ch<=0;out_kind<=0;
     end else frame<=frame+1;
    end else ch<=ch+1;
   end
   if(m_axis_tvalid && m_axis_tready) begin
    if(out_kind==3) begin
     out_kind<=0;
     if(out_ch==CHANNELS-1) begin emitting<=0;out_ch<=0;end
     else out_ch<=out_ch+1;
    end else out_kind<=out_kind+1;
   end
  end
 end
endmodule
