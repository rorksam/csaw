`timescale 1ns/1ps
module tb;
  reg [5:0] phys=0; wire BUSY,ICE_LED,MISO;
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
  task spiw(input[31:0] w); integer i; begin
    `CSN=0; for(i=31;i>=0;i=i-1) begin `MOSI=w[i]; `SCK=1;#10;`SCK=0;#10; end `CSN=1; end endtask
  task rdclk; integer i; begin `CSN=0; for(i=0;i<32;i=i+1) begin `MOSI=0; `SCK=1;#10;`SCK=0;#10; end `CSN=1; end endtask
  task doreset; begin `RSTN=0; pulse; `RSTN=1; pulse; end endtask
  task start; begin `START=1; pulse; `START=0; repeat(7) pulse; end endtask
  `include "dumptask.vh"
  initial begin
    `SCK=0;`RSTN=1;`CSN=1;`START=0;`ENC=0;`MOSI=0; #20;
    // T1: reset, single write, start
    doreset; `ENC=0; spiw(32'h59C359C3); start; dumpff("T1_single");
    // T2: reset, double write, start
    doreset; `ENC=0; spiw(32'h59C359C3); spiw(32'h59C359C3); start; dumpff("T2_double");
    // T3: reset, write, dummy-readout, write, start (= mpy readback)
    doreset; `ENC=0; spiw(32'h59C359C3); rdclk; spiw(32'h59C359C3); start; dumpff("T3_mpy");
    // T4: no reset at all (continue from T3 state), single write, start
    `ENC=0; spiw(32'h59C359C3); start; dumpff("T4_noreset_single");
    // T5: reset, write a DIFFERENT value Q, start, (warmup) then write P start
    doreset; `ENC=0; spiw(32'hA5A5A5A5); start; spiw(32'h59C359C3); start; dumpff("T5_warmup");
    $finish;
  end
  initial begin #80000000 $finish; end
endmodule
