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
  function [7:0] A5;  A5 ={dut.n1985,dut.n2178,dut.n1614,dut.n2776,dut.n2205,dut.n1916,dut.n1929,dut.n2600}; endfunction
  function [7:0] A7;  A7 ={dut.n1494,dut.n2530,dut.n2041,dut.n1540,dut.n1612,dut.n2283,dut.n1784,dut.n2106}; endfunction
  function [7:0] A9;  A9 ={dut.n2139,dut.n2602,dut.n1569,dut.n1788,dut.n2275,dut.n1459,dut.n1605,dut.n1818}; endfunction
  function [7:0] A11; A11={dut.n1743,dut.n2712,dut.n1497,dut.n2533,dut.n1959,dut.n2671,dut.n2397,dut.n2670}; endfunction
  task probe(input[31:0] pp); begin
    doreset; `ENC=0; spiw(pp);
    `START=1; pulse; `START=0;
    $display("IN %08x A5 %02x A7 %02x A9 %02x A11 %02x", pp, A5(),A7(),A9(),A11());
  end endtask
  initial begin
    `SCK=0;`RSTN=1;`CSN=1;`START=0;`ENC=0;`MOSI=0; #20;
    // key = {k3,k2,k1,k0} = 0x8E043CB1 ; feeding p=key should zero ALL lane addresses
    probe(32'h8E043CB1);
    // also each byte alone in its lane -> that lane 0, others at addr(0)
    probe(32'h000000B1);  // byte0=k0
    probe(32'h00003C00);  // byte1=k1
    probe(32'h00040000);  // byte2=k2
    probe(32'h8E000000);  // byte3=k3
    $finish;
  end
  initial begin #50000000 $finish; end
endmodule
