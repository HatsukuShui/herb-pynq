`timescale 1ns/1ps
// Provisional sequential six-command scanner, not simultaneous sampling.
// Contract: each configured 16-bit SPI transaction returns one 16-bit sample.
// Replace for real ADC command, dummy bits, latency, BUSY and CONVST protocol.
module spi_scan_frontend #(parameter CHANNELS=6,HALF_PERIOD=50)(
 input wire clk,rstn,trigger,input wire [CHANNELS*16-1:0] commands,
 input wire miso,output wire sclk,mosi,cs_n,
 output reg busy,frame_valid,output reg [CHANNELS*16-1:0] frame_data,
 output reg overrun);
 reg go;reg [15:0] command;reg [CHANNELS*16-1:0] commands_hold;
 wire transfer_busy,done;wire [15:0] rx;integer ch;reg [1:0] state;
 spi_mode0_master #(.HALF_PERIOD(HALF_PERIOD)) u_spi(clk,rstn,go,command,miso,sclk,mosi,cs_n,transfer_busy,done,rx);
 always @(posedge clk) begin
  if(!rstn) begin busy<=0;frame_valid<=0;frame_data<=0;overrun<=0;go<=0;command<=0;commands_hold<=0;ch<=0;state<=0;end
  else begin
   go<=0;frame_valid<=0;
   if(trigger && busy) overrun<=1;
   case(state)
    0: if(trigger) begin busy<=1;commands_hold<=commands;ch<=0;state<=1;end
    1: begin command<=commands_hold[ch*16+:16];go<=1;state<=2;end
    2: if(done) begin
     frame_data[ch*16+:16]<=rx;
     if(ch==CHANNELS-1) begin busy<=0;frame_valid<=1;state<=0;end
     else begin ch<=ch+1;state<=1;end
    end
   endcase
  end
 end
endmodule
