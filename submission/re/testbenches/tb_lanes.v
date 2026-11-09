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
  `include "getword.vh"
  task enc(input[31:0] p, output[31:0] c); begin
    doreset; `ENC=0; spiw(p); `START=1; pulse; `START=0; repeat(7) pulse; c=getword(); end endtask
  integer n; reg [31:0] c;
  initial begin
    `SCK=0;`RSTN=1;`CSN=1;`START=0;`ENC=0;`MOSI=0; #20;
    // lane independence probe + full tabulation of each lane
    for(n=0;n<256;n=n+1) begin enc(n,c); $display("L0 %02x %08x", n, c); end              // byte0 varies
    for(n=0;n<256;n=n+1) begin enc(n<<8,c); $display("L1 %02x %08x", n, c); end           // byte1
    for(n=0;n<256;n=n+1) begin enc(n<<16,c); $display("L2 %02x %08x", n, c); end          // byte2
    for(n=0;n<256;n=n+1) begin enc(n<<24,c); $display("L3 %02x %08x", n, c); end          // byte3
    $finish;
  end
  initial begin #2000000000 $finish; end
endmodule
