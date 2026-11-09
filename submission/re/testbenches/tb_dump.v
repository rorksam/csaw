`timescale 1ns/1ps
module tb;
  reg [5:0] phys=0;
  wire BUSY,ICE_LED,MISO;
  chip dut(.io_9_31_1(phys[0]),.io_19_31_1(phys[1]),.io_17_31_0(phys[2]),
    .io_16_31_0(phys[3]),.io_13_31_1(phys[4]),.io_18_31_1(phys[5]),
    .io_8_31_1(BUSY),.io_19_31_0(ICE_LED),.io_16_31_1(MISO));
  `define SCK phys[0]
  `define RSTN phys[4]
  `define CSN phys[2]
  `define MOSI phys[3]
  `define ENC phys[1]
  `define START phys[5]
  task pulse; begin `SCK=1;#10;`SCK=0;#10; end endtask
  task wr(input[7:0] b); integer i; begin
    for(i=7;i>=0;i=i-1) begin `MOSI=b[i];#5;`SCK=1;#10;`SCK=0;#5; end end endtask
  `include "dumptask.vh"
  integer c;
  task ingest(input e, input[31:0] d); begin
    `RSTN=0; pulse; `RSTN=1; pulse; `ENC=e;
    `CSN=0; wr(d[31:24]);wr(d[23:16]);wr(d[15:8]);wr(d[7:0]); `CSN=1;
  end endtask
  initial begin
    `SCK=0;`RSTN=1;`CSN=1;`START=0;`ENC=0;`MOSI=0; #20;
    ingest(1'b0,32'h00000000); dumpff("IN0");
    ingest(1'b0,32'hFFFFFFFF); dumpff("INF");
    ingest(1'b0,32'h00000001); dumpff("IN1");
    ingest(1'b0,32'h80000000); dumpff("IN8");
    ingest(1'b0,32'h59C359C3); dumpff("PTlatch");
    `START=1; pulse; `START=0; dumpff("afterSTART");
    for(c=0;c<6;c=c+1) begin dumpff(c==0?"cyc0":(c==1?"cyc1":(c==2?"cyc2":(c==3?"cyc3":(c==4?"cyc4":"cyc5"))))); pulse; end
    $finish;
  end
  initial begin #30000000 $finish; end
endmodule
