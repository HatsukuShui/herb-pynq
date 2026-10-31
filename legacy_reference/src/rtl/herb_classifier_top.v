`timescale 1ns/1ps
// Optional all-PL inference path. Default zero ROMs are a wiring test ONLY.
// Export/retrain model for exact feature order and FEATURE_SHIFT quantization.
module herb_classifier_top #(parameter CLASSES=5,FEATURE_SHIFT=0,
 parameter WEIGHT_FILE="",BIAS_FILE="")(
 input wire aclk,aresetn,
 input wire [31:0] s_axis_tdata,input wire [3:0] s_axis_tkeep,
 input wire s_axis_tvalid,output wire s_axis_tready,input wire s_axis_tlast,
 output wire [31:0] m_axis_tdata,output wire [3:0] m_axis_tkeep,
 output wire m_axis_tvalid,input wire m_axis_tready,output wire m_axis_tlast,
 output wire protocol_error,output reg quantization_overflow);
 wire [31:0] features;wire [3:0] fk;wire fv,fr,fl;wire [7:0] label;
 wire signed [31:0] shifted=$signed(features)>>>FEATURE_SHIFT;
 wire clipped=(shifted>32767 || shifted< -32768);
 wire signed [15:0] quantized=shifted>32767 ? 16'sh7fff : shifted< -32768 ? 16'sh8000 : shifted[15:0];
 herb_axis_core u_features(aclk,aresetn,s_axis_tdata,s_axis_tkeep,s_axis_tvalid,s_axis_tready,s_axis_tlast,
 features,fk,fv,fr,fl,protocol_error);
 linear_classifier #(.CLASSES(CLASSES),.WEIGHT_FILE(WEIGHT_FILE),.BIAS_FILE(BIAS_FILE))
 u_model(aclk,aresetn,quantized,fv,fr,label,m_axis_tvalid,m_axis_tready);
 assign m_axis_tdata={24'b0,label};assign m_axis_tkeep=4'hf;assign m_axis_tlast=m_axis_tvalid;
 always @(posedge aclk) if(!aresetn) quantization_overflow<=0;
 else if(fv && fr && clipped) quantization_overflow<=1;
endmodule
