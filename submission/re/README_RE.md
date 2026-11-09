# Reverse-engineering artifacts & regeneration

How the recovered RTL and golden model were produced from `ice40_bitstream.bin`,
so everything here is reproducible after a fresh `llm4eda up`.

## Files in this directory
- `recovered.v`      — gate-level netlist recovered from the bitstream (module `chip`,
                       iCE40 UP5K, 71 DFFs, 4× SB_RAM40_4K S-boxes). **Primary RE output.**
- `clean_model.v`    — Yosys-flattened behavioral GOLDEN MODEL. Deterministic; reproduces
                       `enc(0x59C359C3)=0x9CD84392` and `dec(0x9CD84392)=0x59C359C3`.
- `E.json`           — the four recovered per-lane substitution tables (complete 256-entry
                       bijections); `lanes.json` = raw per-lane sweep data.
- `testbenches/`     — representative harnesses documenting the RE + cipher analysis
                       (pin-mapping, SPI echo, lane independence, key/address peel).

## Regenerate the two large files (not stored twice)

Run from a shell with the OSS CAD suite on PATH: `source /opt/oss-cad-suite/environment`

```bash
# 1. bitstream -> ASC -> gate netlist
iceunpack ../../ice40_bitstream.bin > design.asc
icebox_vlog design.asc > recovered.v

# 2. sim-friendly copy (fix icebox_vlog output-reg quirk on MISO)
sed -e 's/output io_16_31_1/output reg io_16_31_1/' \
    -e '/^reg io_16_31_1 = 0;/d' recovered.v > recovered_sim.v

# 3. Yosys golden model (clean, initialized, deterministic memories)
CELLS=/opt/oss-cad-suite/share/yosys/ice40/cells_sim.v
yosys -p "read_verilog $CELLS; read_verilog recovered_sim.v; hierarchy -top chip; \
          flatten; proc; memory_collect; opt_clean; write_verilog clean_model.v"
```

## Confirmed pin map (module `chip` ports)
SCK=io_9_31_1, RST_N=io_13_31_1, NORM_CS_N=io_17_31_0, MOSI=io_16_31_0,
ENC_DEC=io_19_31_1, START=io_18_31_1 | BUSY=io_8_31_1, ICE_LED=io_19_31_0, MISO=io_16_31_1.

## Cipher summary
Four byte-INDEPENDENT lanes; each output byte = a keyed 8->8 S-box bijection of the
same input byte (BRAM S-box per lane). Only round 1 is data-dependent (BUSY=4 cycles).
Measured per-lane input-whitening (round-1 S-box address = (byte>>1) XOR off):
lane0 off=0x58, lane1 0x1e, lane2 0x02, lane3 0x47. Full functional spec = E.json.

The clean re-expressed design used for Trojan work is `../rtl/crypto_core.v` (verified
bit-exact to this golden model: 128/128 random vectors + both documented vectors).

## Note on testbenches/tb_final_golden.v
This one drives the GATE golden model over the serial SPI line and shows FAIL — that
is the known 1-bit serial-readout phase offset of the gate netlist (cosmetic). The
golden model is correct at the register level (see tb_mpyexact.v). The authoritative,
fully-passing functional check is the clean design: ../rtl/crypto_core.v with
../pipeline/tb_core.v (both documented vectors PASS + 128/128 random vectors).
