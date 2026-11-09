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
  task spiw(input[7:0] b); integer i; begin
    for(i=7;i>=0;i=i-1) begin `MOSI=b[i]; `SCK=1;#10;`SCK=0;#10; end end endtask
  // read 32 bits: 1 dummy clock to present MSB, then sample-before-edge x32
  task rd32(output [31:0] r); integer i; begin
    r=0;
    for(i=31;i>=0;i=i-1) begin `MOSI=0; `SCK=1; #5; r[i]=MISO; #5; `SCK=0; #10; end
  end endtask
  reg [31:0] rb,ct,pt;
  initial begin
    `SCK=0;`RSTN=1;`CSN=1;`START=0;`ENC=0;`MOSI=0; #20;
    `RSTN=0; pulse; `RSTN=1; pulse;
    // readback preconditioning (writes plaintext twice, as MicroPython)
    `CSN=0; spiw(8'h59);spiw(8'hC3);spiw(8'h59);spiw(8'hC3); `CSN=1;
    `CSN=0; spiw(8'h59);spiw(8'hC3);spiw(8'h59);spiw(8'hC3); `CSN=1;
    // ENCRYPT (no reset)
    `ENC=0; `START=1; pulse; `START=0; repeat(7) pulse;
    `CSN=0; rd32(ct); `CSN=1;
    $display("ENCRYPT 0x59C359C3 -> 0x%08x  [%s]", ct, (ct==32'h9CD84392)?"PASS":"FAIL");
    // DECRYPT (reset first)
    `ENC=1; `RSTN=0; pulse; `RSTN=1; pulse;
    `CSN=0; spiw(8'h9C);spiw(8'hD8);spiw(8'h43);spiw(8'h92); `CSN=1;
    `START=1; pulse; `START=0; repeat(7) pulse;
    `CSN=0; rd32(pt); `CSN=1;
    $display("DECRYPT 0x9CD84392 -> 0x%08x  [%s]", pt, (pt==32'h59C359C3)?"PASS":"FAIL");
    $finish;
  end
  initial begin #60000000 $finish; end
endmodule
