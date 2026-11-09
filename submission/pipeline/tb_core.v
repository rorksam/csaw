`timescale 1ns/1ps
// Verification TB for the clean base crypto_core: documented vectors + random sweep.
module tb;
  reg SCK=0,RST_N=1,MOSI=0,NORM_CS_N=1,START=0,ENC_DEC=0;
  wire MISO,BUSY,ICE_LED;
  crypto_core dut(.SCK(SCK),.RST_N(RST_N),.MOSI(MOSI),.MISO(MISO),
    .NORM_CS_N(NORM_CS_N),.START(START),.ENC_DEC(ENC_DEC),.BUSY(BUSY),.ICE_LED(ICE_LED));
  task pulse; begin SCK=1;#10;SCK=0;#10; end endtask
  task wr(input [31:0] w); integer i; begin
    NORM_CS_N=0;
    for(i=31;i>=0;i=i-1) begin MOSI=w[i]; pulse; end
    NORM_CS_N=1;
  end endtask
  task op(input e, input [31:0] p, output [31:0] c); integer i; begin
    RST_N=0; pulse; RST_N=1; pulse;
    ENC_DEC=e; wr(p);
    START=1; pulse; START=0;
    repeat(5) pulse;              // 4-cycle BUSY + load
    NORM_CS_N=0; c=0;
    for(i=31;i>=0;i=i-1) begin c[i]=MISO; pulse; end
    NORM_CS_N=1;
  end endtask
  integer n,seed; reg [31:0] p,c;
  initial begin
    seed=1;
    op(1'b0,32'h59C359C3,c);
    $display("ENC 59C359C3 -> %08x %s",c,(c==32'h9CD84392)?"PASS":"FAIL");
    op(1'b1,32'h9CD84392,c);
    $display("DEC 9CD84392 -> %08x %s",c,(c==32'h59C359C3)?"PASS":"FAIL");
    // random sweep: print for external check against cipher tables
    for(n=0;n<64;n=n+1) begin
      p=$random(seed);
      op(1'b0,p,c); $display("RND E %08x %08x",p,c);
      op(1'b1,p,c); $display("RND D %08x %08x",p,c);
    end
    $finish;
  end
  initial begin #5000000 $finish; end
endmodule
