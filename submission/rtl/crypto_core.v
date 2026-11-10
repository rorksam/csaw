// =============================================================================
// crypto_core.v  -  Reverse-engineered Hackster iCE40 lightweight crypto IP
//
// Recovered from ice40_bitstream.bin (CSAW HW-Trojan challenge). The core is a
// 32-bit SPI-peripheral block cipher: four byte-wide lanes, each an independent
// keyed 8->8 bijection realised as a block-RAM S-box. ENC_DEC selects the
// forward (encrypt) or inverse (decrypt) substitution table per lane.
//
// Behaviour validated bit-exact against the Yosys golden model of the bitstream:
//   encrypt(0x59C359C3) = 0x9CD84392 ,  decrypt(0x9CD84392) = 0x59C359C3
//
// Clean, synthesizable re-expression (the challenge permits renaming/restructure).
// This is the BASE design into which the automated pipeline inserts Trojans.
// =============================================================================
`default_nettype none

module crypto_core (
    input  wire        SCK,        // unified SPI + system clock (<=1 MHz)
    input  wire        RST_N,      // synchronous active-low reset
    input  wire        MOSI,       // serial data in
    output wire        MISO,       // serial data out
    input  wire        NORM_CS_N,  // active-low chip select / shift enable
    input  wire        START,      // pulse: begin encrypt/decrypt
    input  wire        ENC_DEC,    // 0 = encrypt, 1 = decrypt
    output wire        BUSY,       // high while processing
    output wire        ICE_LED     // mirror of BUSY
);

    localparam [2:0] LATENCY = 3'd4;    // processing takes 4 SCK cycles

    reg [31:0] shift_reg;               // SPI shift register / data register
    reg [31:0] operand;                 // latched word being processed
    reg        mode;                    // latched ENC_DEC for current op
    reg [2:0]  busy_cnt;                // counts down the processing latency

    // ---- per-lane substitution tables (block-RAM S-boxes) ------------------
    reg [7:0] sbox_enc0 [0:255]; reg [7:0] sbox_dec0 [0:255];
    reg [7:0] sbox_enc1 [0:255]; reg [7:0] sbox_dec1 [0:255];
    reg [7:0] sbox_enc2 [0:255]; reg [7:0] sbox_dec2 [0:255];
    reg [7:0] sbox_enc3 [0:255]; reg [7:0] sbox_dec3 [0:255];
    initial begin
        $readmemh("rom_enc0.hex", sbox_enc0); $readmemh("rom_dec0.hex", sbox_dec0);
        $readmemh("rom_enc1.hex", sbox_enc1); $readmemh("rom_dec1.hex", sbox_dec1);
        $readmemh("rom_enc2.hex", sbox_enc2); $readmemh("rom_dec2.hex", sbox_dec2);
        $readmemh("rom_enc3.hex", sbox_enc3); $readmemh("rom_dec3.hex", sbox_dec3);
    end

    // ---- combinational cipher: 4 independent byte lanes --------------------
    // Note: one declaration per lane (not a comma-separated list) so the design
    // parses cleanly under PyVerilog, which the GNN stealth gate uses to build
    // the exact dataflow graph. Semantically identical to a single wire list.
    wire [7:0] p0 = operand[7:0];
    wire [7:0] p1 = operand[15:8];
    wire [7:0] p2 = operand[23:16];
    wire [7:0] p3 = operand[31:24];
    wire [7:0] c0 = mode ? sbox_dec0[p0] : sbox_enc0[p0];
    wire [7:0] c1 = mode ? sbox_dec1[p1] : sbox_enc1[p1];
    wire [7:0] c2 = mode ? sbox_dec2[p2] : sbox_enc2[p2];
    wire [7:0] c3 = mode ? sbox_dec3[p3] : sbox_enc3[p3];
    wire [31:0] cipher_out = {c3, c2, c1, c0};

    // ---- control / datapath -------------------------------------------------
    always @(posedge SCK) begin
        if (!RST_N) begin
            shift_reg <= 32'd0;
            busy_cnt  <= 3'd0;
            operand   <= 32'd0;
            mode      <= 1'b0;
        end else if (busy_cnt != 3'd0) begin
            // processing: count down; on completion parallel-load the result
            busy_cnt <= busy_cnt - 3'd1;
            if (busy_cnt == 3'd1)
                shift_reg <= cipher_out;
        end else if (START) begin
            // kick off a new operation on the currently-loaded word
            operand  <= shift_reg;
            mode     <= ENC_DEC;
            busy_cnt <= LATENCY;
        end else if (!NORM_CS_N) begin
            // SPI shift: MSB-first in on MOSI, MSB-first out on MISO
            shift_reg <= {shift_reg[30:0], MOSI};
        end
    end

    assign MISO    = shift_reg[31];
    assign BUSY    = (busy_cnt != 3'd0);
    assign ICE_LED = BUSY;

endmodule

`default_nettype wire
