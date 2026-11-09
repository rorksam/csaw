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
  task doreset; begin `RSTN=0; pulse; `RSTN=1; pulse; end endtask
  // lane0 = ram40_6_5 : addr bundle + data
  function [6:0] a5; a5={dut.n2178,dut.n1614,dut.n2776,dut.n2205,dut.n1916,dut.n1929,dut.n2600}; endfunction
  integer n;
  initial begin
    `SCK=0;`RSTN=1;`CSN=1;`START=0;`ENC=0;`MOSI=0; #20;
    for(n=0;n<256;n=n+1) begin
      doreset; `ENC=0; spiw(n);
      `START=1; pulse; `START=0;
      // c0..c3 = rounds 1..4; capture addr & data each
      $write("p0=%02x", n);
      $write(" A1=%02x D1=%04x", a5(), dut._0077_); pulse;
      $write(" A2=%02x D2=%04x", a5(), dut._0077_); pulse;
      $write(" A3=%02x D3=%04x", a5(), dut._0077_); pulse;
      $write(" A4=%02x D4=%04x", a5(), dut._0077_); pulse;
      $write("\n");
    end
    $finish;
  end
  initial begin #200000000 $finish; end
endmodule
