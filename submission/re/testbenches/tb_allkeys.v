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
  function [6:0] a5;  a5 ={dut.n2178,dut.n1614,dut.n2776,dut.n2205,dut.n1916,dut.n1929,dut.n2600}; endfunction
  function [6:0] a7;  a7 ={dut.n2530,dut.n2041,dut.n1540,dut.n1612,dut.n2283,dut.n1784,dut.n2106}; endfunction
  function [6:0] a9;  a9 ={dut.n2602,dut.n1569,dut.n1788,dut.n2275,dut.n1459,dut.n1605,dut.n1818}; endfunction
  function [6:0] a11; a11={dut.n2712,dut.n1497,dut.n2533,dut.n1959,dut.n2671,dut.n2397,dut.n2670}; endfunction
  task probe(input[31:0] pp); begin
    doreset; `ENC=0; spiw(pp); `START=1; pulse; `START=0;
    $display("in=%08x a5=%02x a7=%02x a9=%02x a11=%02x", pp, a5(),a7(),a9(),a11());
  end endtask
  integer b;
  initial begin
    `SCK=0;`RSTN=1;`CSN=1;`START=0;`ENC=0;`MOSI=0; #20;
    probe(0);
    // single bits in each byte lane
    for(b=0;b<8;b=b+1) probe(32'h1<<b);        // byte0
    for(b=0;b<8;b=b+1) probe(32'h100<<b);      // byte1
    for(b=0;b<8;b=b+1) probe(32'h10000<<b);    // byte2
    for(b=0;b<8;b=b+1) probe(32'h1000000<<b);  // byte3
    $finish;
  end
  initial begin #120000000 $finish; end
endmodule
