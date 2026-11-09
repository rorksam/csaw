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
  // SoftSPI write (mode0 MSB-first): sets MOSI while low, pulses
  task spiw(input[7:0] b); integer i; begin
    for(i=7;i>=0;i=i-1) begin `MOSI=b[i]; `SCK=1;#10;`SCK=0;#10; end end endtask
  `include "dumptask.vh"
  initial begin
    `SCK=0;`RSTN=1;`CSN=1;`START=0;`ENC=0;`MOSI=0; #20;
    // reset the core (mpy)
    `RSTN=0; `SCK=1;#10;`SCK=0;#10; `RSTN=1; `SCK=1;#10;`SCK=0;#10;
    // SPI readback test: write plaintext, then write_readinto (write plaintext again)
    `CSN=0; spiw(8'h59);spiw(8'hC3);spiw(8'h59);spiw(8'hC3); `CSN=1;
    `CSN=0; spiw(8'h59);spiw(8'hC3);spiw(8'h59);spiw(8'hC3); `CSN=1;
    dumpff("afterReadback");
    // encryption test (NO reset)
    `ENC=0;
    `START=1; `SCK=1;#10;`SCK=0;#10; `START=0;
    dumpff("afterStart");
    // range(7) clocks
    repeat(7) pulse;
    dumpff("beforeRead");
    $finish;
  end
  initial begin #60000000 $finish; end
endmodule
