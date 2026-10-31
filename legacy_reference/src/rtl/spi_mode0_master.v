`timescale 1ns/1ps
// Generic transport ONLY, not an ADC-specific command driver.
// CPOL=0, CPHA=0, MSB first. MISO synchronous to generated slow SCLK.
module spi_mode0_master #(parameter WIDTH=16, HALF_PERIOD=50)(
 input wire clk,rstn,start, input wire [WIDTH-1:0] tx_data,
 input wire miso, output reg sclk,mosi,cs_n,busy,done,
 output reg [WIDTH-1:0] rx_data);
 integer divider,bit_index;
 reg [WIDTH-1:0] tx_hold,rx_shift;
 always @(posedge clk) begin
  if(!rstn) begin sclk<=0;mosi<=0;cs_n<=1;busy<=0;done<=0;
   divider<=0;bit_index<=0;tx_hold<=0;rx_shift<=0;rx_data<=0;end
  else begin
   done<=0;
   if(!busy) begin
    if(start) begin busy<=1;cs_n<=0;sclk<=0;divider<=0;
     tx_hold<=tx_data;mosi<=tx_data[WIDTH-1];bit_index<=WIDTH-1;rx_shift<=0;end
   end else if(divider==HALF_PERIOD-1) begin
    divider<=0;
    if(!sclk) begin sclk<=1;rx_shift<={rx_shift[WIDTH-2:0],miso};end
    else begin
     sclk<=0;
     if(bit_index==0) begin cs_n<=1;busy<=0;done<=1;rx_data<=rx_shift;end
     else begin bit_index<=bit_index-1;mosi<=tx_hold[bit_index-1];end
    end
   end else divider<=divider+1;
  end
 end
endmodule
