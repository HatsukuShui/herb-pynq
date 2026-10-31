`timescale 1ns/1ps
module tb_core;
 reg clk=0;always #5 clk=~clk;
 reg rstn=0;reg [31:0] din=0;reg vin=0,lin=0,rout=0;
 wire rin,vout,lout,err;wire [31:0] dout;wire [3:0] keep;
 reg [31:0] samples[0:671],expected[0:71];
 integer sent=0,received=0,cycles=0;reg [31:0] rng=32'h12345678;
 reg stalled=0;reg [31:0] held;reg held_last;reg accepted=0;
 herb_axis_core dut(clk,rstn,din,4'hf,vin,rin,lin,dout,keep,vout,rout,lout,err);
 initial begin
  $readmemh("data/replay_input.mem",samples);$readmemh("data/replay_expected.mem",expected);
  repeat(5) @(negedge clk);rstn=1;
 end
 always @(negedge clk) if(rstn) begin
  rng={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};rout=rng[3];
  if(!vin || accepted) begin
   vin=(sent<672 && rng[7]);
   if(vin) begin din=samples[sent];lin=(sent==287 || sent==479 || sent==671);end
  end
 end
 always @(posedge clk) if(rstn) begin
  cycles=cycles+1;
  accepted=vin && rin;
  if(accepted) sent=sent+1;
  if(stalled && (!vout || dout!==held || lout!==held_last)) $fatal(1,"AXIS changed under stall");
  stalled=vout && !rout;held=dout;held_last=lout;
  if(err) $fatal(1,"Unexpected protocol error");
  if(vout && rout) begin
   if(dout!==expected[received]) $fatal(1,"word %0d got %h expected %h",received,dout,expected[received]);
   if(lout !== (received%24==23) || keep!==4'hf) $fatal(1,"packet framing error");
   received=received+1;
   if(received==72) begin $display("PASS core: 672 real input words, 72 features, random stalls, 3 packets");$finish;end
  end
  if(cycles>10000) $fatal(1,"timeout");
 end
endmodule
