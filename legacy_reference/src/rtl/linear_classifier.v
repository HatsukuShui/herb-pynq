`timescale 1ns/1ps
// Sequential dot product; one signed 16x16 multiplier shared across classes.
// Parameters are compile-time ROM. Empty files give zero weights: NOT trained.
// FEATURES<=256, CLASSES<=256. bias in product units; scores signed 48 bits.
module linear_classifier #(parameter FEATURES=24,CLASSES=5,
 parameter WEIGHT_FILE="",BIAS_FILE="")(
 input wire clk,rstn,input wire signed [15:0] feature_data,
 input wire feature_valid,output wire feature_ready,
 output reg [7:0] class_id,output reg result_valid,input wire result_ready);
 reg signed [15:0] weights[0:FEATURES*CLASSES-1],features[0:FEATURES-1];
 reg signed [47:0] biases[0:CLASSES-1];
 reg signed [47:0] acc,best;
 wire signed [31:0] product=features[k]*weights[c*FEATURES+k];
 wire signed [47:0] total=acc+{{16{product[31]}},product};
 reg computing;integer n,k,c,i;
 initial begin
  for(i=0;i<FEATURES*CLASSES;i=i+1) weights[i]=0;
  for(i=0;i<CLASSES;i=i+1) biases[i]=0;
  if(WEIGHT_FILE!="") $readmemh(WEIGHT_FILE,weights);
  if(BIAS_FILE!="") $readmemh(BIAS_FILE,biases);
 end
 assign feature_ready=!computing && !result_valid;
 always @(posedge clk) begin
  if(!rstn) begin n<=0;k<=0;c<=0;computing<=0;result_valid<=0;class_id<=0;acc<=0;best<=0;end
  else begin
   if(result_valid && result_ready) result_valid<=0;
   if(feature_valid && feature_ready) begin
    features[n]<=feature_data;
    if(n==FEATURES-1) begin n<=0;k<=0;c<=0;computing<=1;acc<=biases[0];end
    else n<=n+1;
   end
   if(computing) begin
    if(k==FEATURES-1) begin
     if(c==0 || total>best) begin best<=total;class_id<=c;end
     k<=0;
     if(c==CLASSES-1) begin computing<=0;result_valid<=1;end
     else begin c<=c+1;acc<=biases[c+1];end
    end else begin acc<=total;k<=k+1;end
   end
  end
 end
endmodule
