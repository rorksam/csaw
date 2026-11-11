# Trojan pipeline run

- generation: LLM
- GNN detector gate: ready (margin 0.3, weight 0.15)
- candidates: 3  | best: **magic-operand-leak** (score 100.0)
- base footprint: 68 LUT4 / 1 DFF

| rank | name | score | stealth | payload | lutΔ | dffΔ | gnnP(troj) | evades | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | magic-operand-leak | 100.0 | 1.0 | True | 0 | 0 | 0.283 | None | ok |
| 2 | operand-selftrig-x4 | 0.0 | 1.0 | True | 0 | 0 | 0.460 | None | weak |
| 3 | operand-selftrig-x4 | 0.0 | 1.0 | True | 0 | 0 | 0.283 | None | weak |

## Best candidate
- trigger: When an encrypt/decrypt operation is started on the exact 32-bit operand 0xA5A5F00F (loaded via SPI then START), the core is triggered. Any other operand value produces the normal bit-exact result.
- payload: On the trigger operand, instead of the normal cipher_out the core loads a fixed leak constant 0xDEADC0DE into the shift register, which is then clocked out MSB-first on MISO. Observable directly as the readback word.
- trigger outputs: ['deadc0de'] (oracle would give ['4f92f627'])
- GNN: verdict=CLEAN votes=0 max_P(trojan)=0.283 evades=None
