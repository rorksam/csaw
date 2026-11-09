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
  // address bundles (MSB..LSB as in concat)
  function [6:0] a11; a11={dut.n2712,dut.n1497,dut.n2533,dut.n1959,dut.n2671,dut.n2397,dut.n2670}; endfunction
  function [6:0] a5;  a5 ={dut.n2178,dut.n1614,dut.n2776,dut.n2205,dut.n1916,dut.n1929,dut.n2600}; endfunction
  function [6:0] a7;  a7 ={dut.n2530,dut.n2041,dut.n1540,dut.n1612,dut.n2283,dut.n1784,dut.n2106}; endfunction
  function [6:0] a9;  a9 ={dut.n2602,dut.n1569,dut.n1788,dut.n2275,dut.n1459,dut.n1605,dut.n1818}; endfunction
  integer n; reg [31:0] p;
  task probe(input[31:0] pp); begin
    doreset; `ENC=0; spiw(pp);
    `START=1; pulse; `START=0;
    // at c0 (round1) capture addresses
    $display("in=%08x c0: a11=%02x a5=%02x a7=%02x a9=%02x | d11=%04x d5=%04x d7=%04x d9=%04x",
      pp, a11(),a5(),a7(),a9(), dut._0072_,dut._0077_,dut._0082_,dut._0087_);
  end endtask
  initial begin
    `SCK=0;`RSTN=1;`CSN=1;`START=0;`ENC=0;`MOSI=0; #20;
    probe(32'h00000000);
    probe(32'h00000001); probe(32'h00000002); probe(32'h00000004); probe(32'h00000008);
    probe(32'h00000010); probe(32'h00000020); probe(32'h00000040); probe(32'h00000080);
    probe(32'h000000FF); probe(32'h0000005A);
    $finish;
  end
  initial begin #80000000 $finish; end
endmodule
