`timescale 1ns/1ps
// Find the SPI shift plumbing via the MicroPython echo oracle:
// shift W1 in, then clock out and expect W1 back. Crypto not involved.
module tb;
  reg [5:0] phys=0;
  wire BUSY,ICE_LED,MISO;
  chip dut(.io_9_31_1(phys[0]),.io_19_31_1(phys[1]),.io_17_31_0(phys[2]),
    .io_16_31_0(phys[3]),.io_13_31_1(phys[4]),.io_18_31_1(phys[5]),
    .io_8_31_1(BUSY),.io_19_31_0(ICE_LED),.io_16_31_1(MISO));
  integer P_RST,P_CS,P_MOSI,P_START,P_ENC;
  integer ORD; // 0=MSB-first, 1=LSB-first on MOSI
  task tick; begin phys[0]=1;#10;phys[0]=0;#10; end endtask

  reg [63:0] stream;
  reg [31:0] W1;

  task shift_in(input [31:0] w);
    integer i; begin
      phys[P_CS]=0;
      for(i=0;i<32;i=i+1) begin
        phys[P_MOSI]= (ORD==0)? (w>>(31-i))&1 : (w>>i)&1;
        #10; tick;
      end
      phys[P_CS]=1; tick;
    end
  endtask

  task read_out;
    integer i; begin
      phys[P_CS]=0; stream=0;
      for(i=0;i<64;i=i+1) begin phys[P_MOSI]=0;#5; stream={stream[62:0],MISO};#5; tick; end
      phys[P_CS]=1;
    end
  endtask

  function [31:0] rev32(input [31:0] x); integer i; begin
    for(i=0;i<32;i=i+1) rev32[i]=x[31-i]; end endfunction

  function integer win(input [63:0] s,input[31:0] t); integer o; begin
    win=-1; for(o=0;o<=32;o=o+1) if(((s>>o)&32'hFFFFFFFF)===t) win=o; end endfunction

  integer a,b,c,d,e,o1,o2,nf;
  initial begin
    W1=32'h59C359C3; nf=0;
    for (ORD=0;ORD<=1;ORD=ORD+1)
    for (a=1;a<=5;a=a+1) for(b=1;b<=5;b=b+1) if(b!=a)
    for (c=1;c<=5;c=c+1) if(c!=a&&c!=b)
    for (d=1;d<=5;d=d+1) if(d!=a&&d!=b&&d!=c)
    for (e=1;e<=5;e=e+1) if(e!=a&&e!=b&&e!=c&&e!=d) begin
      P_RST=a;P_CS=b;P_MOSI=c;P_START=d;P_ENC=e;
      // reset + idle
      phys[1]=0;phys[2]=0;phys[3]=0;phys[4]=0;phys[5]=0; tick;tick;
      phys[P_RST]=1;phys[P_CS]=1;phys[P_START]=0;phys[P_ENC]=0; tick;
      phys[P_RST]=0; tick; phys[P_RST]=1; tick;
      shift_in(W1);
      read_out;
      o1=win(stream,W1); o2=win(stream,rev32(W1));
      if (o1>=0 || o2>=0) begin
        $display("ECHO ord=%0d RST=%0d CS=%0d MOSI=%0d START=%0d ENC=%0d | norm@%0d rev@%0d stream=%016x",
                 ORD,a,b,c,d,e,o1,o2,stream);
        nf=nf+1;
      end
    end
    $display("done echoes=%0d",nf);
    $finish;
  end
  initial begin #400000000 $display("TIMEOUT"); $finish; end
endmodule
