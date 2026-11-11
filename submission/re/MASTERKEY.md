# Master key recovery — CSAW iCE40 crypto core

**Master key: `0x8E043CB1`** (32-bit, same byte convention as the documented
plaintext word `0x59C359C3`).

| lane | plaintext byte      | key byte | binary      |
|------|---------------------|----------|-------------|
| 0    | `operand[7:0]`      | `0xB1`   | `1011 0001` |
| 1    | `operand[15:8]`     | `0x3C`   | `0011 1100` |
| 2    | `operand[23:16]`    | `0x04`   | `0000 0100` |
| 3    | `operand[31:24]`    | `0x8E`   | `1000 1110` |

SPI byte stream (MSB-first, as the reference driver transmits): `8E 04 3C B1`.

## Structure

Each lane is a single-round **AddRoundKey → SubBytes**: the plaintext byte is
XORed with the lane key byte, and the result (after a fixed bit-permutation from
place-and-route) indexes that lane's block-RAM S-box:

```
addr_i = perm( p_i XOR k_i )          (perm: input bit0 -> addr MSB, bit j -> addr bit j-1)
c_i    = outwiring_i( ROM[ addr_i ] )
```

All four BRAMs hold the identical INIT; the four lanes differ by their key byte
`k_i` (input whitening) and a per-lane output-bit wiring. The complete per-lane
input→output tables are in `E.json` (full functional break).

## How it was recovered (reproducible)

The key is the input whitening, recovered directly from the round-1 ROM address
nets in the golden model `clean_model.v` — not guessed:

1. `testbenches/tb_fullkey.v` — drives plaintext `0` and all 32 one-hot inputs,
   capturing the full 8-bit data address of each lane's BRAM
   (`A5,A7,A9,A11` = lanes 0..3). This gives:
   - `addr(p=0) = perm(k)` per lane: `d8, 1e, 02, 47`
   - the input→address bit-permutation (identical on every lane):
     input bit0 → addr bit7, input bit j → addr bit (j-1).
   De-permuting `addr(0)` yields the key bytes above, LSB included.

2. `testbenches/tb_verify.v` — **proof**: feeding `p = 0x8E043CB1` drives every
   lane address to `0x00` (`perm(k XOR k)=0`), and each key byte alone nulls only
   its own lane. Exact, unambiguous confirmation.

```bash
source /opt/oss-cad-suite/environment
iverilog -g2012 -o /tmp/fk.vvp clean_model.v testbenches/tb_fullkey.v && vvp /tmp/fk.vvp
iverilog -g2012 -o /tmp/vf.vvp clean_model.v testbenches/tb_verify.v  && vvp /tmp/vf.vvp
#   IN 8e043cb1 A5 00 A7 00 A9 00 A11 00   <- all lane addresses zeroed
```

## Note on the earlier 7-bit result

A prior pass measured only the 7 high address bits per byte
(`off = {0x58,0x1e,0x02,0x47} = k>>1`), leaving bit0 of each key byte open
(candidates `{B0,3C,04,8E}`). Capturing the full 8-bit data address (the extra
`bit8`/byte-select net, which carries plaintext bit0 XOR key bit0) resolves it:
only `k0` has bit0 set, giving `{B1,3C,04,8E}`.
