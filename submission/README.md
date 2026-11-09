# CSAW Hardware-Trojan Challenge — Technical Brief

> **Status: work-in-progress report.** Reverse engineering, cipher analysis, and the
> full agentic Trojan-insertion pipeline are complete and validated. The final
> LLM-*generated* Trojan population is produced by running the pipeline notebook
> (next step); a hand-authored **reference Trojan** is included and scored end-to-end
> to demonstrate the whole flow working.

Target: a Lattice **iCE40 UltraPlus UP5K** FPGA ("Hackster" board) acting as an SPI
**peripheral** lightweight crypto accelerator, driven by an RP2040 SPI controller.
Only three inputs were permitted — the interface doc, the RP2040 test script, and the
**bitstream** (`ice40_bitstream.bin`). The source RTL was withheld and had to be
recovered from the bitstream.

---

## 1 · Reverse-engineering method

**Toolchain:** OSS CAD Suite — Project IceStorm (`iceunpack`), `icebox_vlog`, Yosys,
Icarus Verilog. Fully reproducible from the bitstream; see `re/README_RE.md`.

```
ice40_bitstream.bin ──iceunpack──► design.asc ──icebox_vlog──► re/recovered.v   (gate netlist)
                                                     │ Yosys flatten + memory_collect
                                                     ▼
                                              re/clean_model.v                   (golden model)
                                                     │ functional re-expression
                                                     ▼
                                              rtl/crypto_core.v                  (clean base RTL)
```

1. **Bitstream → gate netlist.** `iceunpack` + `icebox_vlog` recovered module `chip`
   (iCE40 UP5K primitives: **4× `SB_RAM40_4K`** block RAMs = the S-boxes, plus DFF/LUT
   control logic). This is the primary RE artifact, `re/recovered.v`.
2. **Pin map.** The netlist's opaque `io_r_c_b` ports were mapped to the documented
   interface by cross-referencing the interface doc and the RP2040 pin assignments:

   | signal | netlist port | | signal | netlist port |
   |---|---|---|---|---|
   | `SCK` | `io_9_31_1` | | `MISO` | `io_16_31_1` |
   | `RST_N` | `io_13_31_1` | | `BUSY` | `io_8_31_1` |
   | `MOSI` | `io_16_31_0` | | `ICE_LED` | `io_19_31_0` |
   | `NORM_CS_N` | `io_17_31_0` | | `ENC_DEC` | `io_19_31_1` |
   | `START` | `io_18_31_1` | | | |

3. **Golden model.** Yosys `flatten; proc; memory_collect; opt_clean` produced a
   deterministic behavioral model (`re/clean_model.v`) with initialized memories,
   used as the simulation oracle.
4. **Validation.** The golden model reproduces both documented vectors:
   `enc(0x59C359C3) = 0x9CD84392` and `dec(0x9CD84392) = 0x59C359C3`.
5. **Clean re-expression.** The design was re-authored as a readable, synthesizable
   module `rtl/crypto_core.v` (the challenge permits renaming/restructuring). It is
   verified **bit-exact** to the golden model: both documented vectors **plus 128/128
   random vectors** match. This is the base into which Trojans are inserted.

---

## 2 · How the encryption works (proposed explanation)

The core is **not** a conventional round-mixing block cipher — it is **four
byte-independent keyed substitution lanes**:

```
E(P) = E3(p3) ‖ E2(p2) ‖ E1(p1) ‖ E0(p0)      P = p3‖p2‖p1‖p0 (bytes)
```

- **Lane independence verified:** flipping any single input byte changes **only** the
  same output byte — so each lane is an independent 8→8 bijection, realised as one of
  the four block-RAM S-boxes. `ENC_DEC` selects the forward or inverse table per lane.
- **Latency:** `BUSY` is high for 4 `SCK` cycles, but probing shows **only round 1 is
  data-dependent** (addresses/data on rounds 2–4 are constant across inputs) — i.e.
  effectively a single keyed S-box lookup per lane, padded to a 4-cycle pipeline.
- **Complete functional break:** the four 256-entry lane tables `E0..E3` are fully
  recovered in `re/E.json` / `pipeline/cipher_tables.json`. Sanity:
  `enc(0x59C359C3)=0x9CD84392` ✓ and `enc(0)=0x08ABD043` ✓.

### Key recovery (bonus +10 — partial, documented)

The round-1 S-box address is affine in the input: `addr_i = (p_i >> 1) XOR off_i`.
Measuring `off_i` per lane gives the **input-whitening key material**:

| lane | byte | S-box BRAM | offset `off_i` | candidate key byte (bit0 = byte-select) |
|---|---|---|---|---|
| 0 | `operand[7:0]`   | `ram40_6_5`  | `0x58` | `0xB0` |
| 1 | `operand[15:8]`  | `ram40_6_7`  | `0x1e` | `0x3C` |
| 2 | `operand[23:16]` | `ram40_6_9`  | `0x02` | `0x04` |
| 3 | `operand[31:24]` | `ram40_6_11` | `0x47` | `0x8E` |

`off_i = (k_i >> 1)`, so the high 7 bits of each key byte are known; bit 0 is the raw
(unkeyed) byte-select into the 16-bit BRAM word, which is why the lanes are not
affine-equivalent and the exact master key bit-0s are not cleanly separable from the
flattened model. **Strongest clean deliverables:** (1) the complete per-lane
substitution tables `E0..E3` (full functional break), and (2) the measured key
material `{0x58, 0x1e, 0x02, 0x47}`. Exact per-bit master-key extraction would trace
the *un-flattened* `recovered.v` (rounds intact) — noted as future work.

---

## 3 · AI method (the agentic Trojan-insertion pipeline)

The centrepiece is **`pipeline/trojan_feedback_pipeline.ipynb`** — a one-click,
closed-loop *generate → insert → verify → score → refine* pipeline. It is
**provider-agnostic** (Anthropic + OpenAI) and every verification stage runs with no
API key, so the loop is always reproducible.

```
           ┌──────────────┐   feedback: scorecard + sim diffs + AST diagnostics
           │ LLM GENERATE │◄──────────────────────────────────────────────┐
           │ Anthropic /  │                                                │
           │  OpenAI      │  candidate {rtl, trigger_program, expected}    │
           └──────┬───────┘                                                │
                  ▼                                                        │
   ┌──────────────────────────┐    ┌────────────────────────────────────┐│
   │ AST GATE (pyslang)        │──► │ SCORER                             │┘
   │  parse + elaborate        │    │  stealth 40  (oracle × 128 vectors)│
   │  + enforce ports unchanged│    │  payload 30  (trigger program)     │
   └──────────────────────────┘    │  specificity 15 (false-trigger)    │
                                    │  footprint 15 (yosys synth_ice40)  │
                                    └────────────────────────────────────┘
```

**Pipeline stages (all validated):**

| stage | tool | what it does |
|---|---|---|
| Golden oracle | pure Python | reference `E/D` from recovered tables; stealth ground truth |
| Sim harness | Icarus Verilog | command-driven SPI TB (`R`/`E`/`D` programs, state preserved across ops → supports sequential Trojans) |
| Footprint | Yosys `synth_ice40` | iCE40 cell counts; base = **141 LUT4 / 68 DFF / 8 RAM40 / 1 CARRY** |
| **AST gate** | **pyslang 12.1.0** | parse + semantic **elaborate** (`Compilation.getAllDiagnostics`) and enforce module name + exact port list are unchanged — the Trojan may not alter the SPI interface |
| Scorer | all of the above | single weighted scorecard with hard gates (AST / interface / compile / functional) |
| Structured inserter | anchor splice | deterministic AST-located Trojan insertion + offline seed generator |
| Generator | Anthropic / OpenAI | provider-agnostic client; structured JSON candidate contract |
| **Refine loop** | — | feeds each scorecard + simulation diffs back to the model to improve the next candidate; keeps the best |

**Why this scores on "creative AI use":** candidates are gated at the **AST/semantic
level** (pyslang elaboration + port-set equality), not by string matching; generation
is **multi-model**; and the loop is a genuine **feedback/refinement agent** rather than
one-shot prompting. The verification oracle is derived from the *reverse-engineered
cipher itself*, so "normal operation preserved" is checked against the real function.

**Reproducibility:** `pip install -r pipeline/requirements.txt` (pyslang, anthropic,
openai; EDA tools ship in the lab image). Run the notebook top-to-bottom. Setting
`TROJAN_ENABLE_LLM=0` forces the offline seed-bank path for a key-free CI run.
Artifacts land in `pipeline/pipeline_out/` (best RTL, `scorecards.json`, `RUN_SUMMARY.md`).

---

## 4 · Trojan design — reference example (demonstrates the flow)

The pipeline's scorer is validated end-to-end against a hand-authored reference
Trojan (the LLM-generated population is produced later by running the loop):

- **Trigger:** a **magic plaintext word** (`0xDEADBEEF`) presented to an *encrypt*
  operation. Chosen so it never arises in normal traffic — **false-trigger
  probability ≈ 2⁻³²**; measured false-trigger rate over 128 random vectors = **0**.
- **Payload:** on the trigger, the operation returns a **constant leak word
  (`0x8E043CB0`, the recovered key-byte candidates) on MISO** instead of the true
  ciphertext — a **key-exfiltration** payload. All other traffic is bit-exact to the
  original.
- **Stealth / footprint:** normal encrypt/decrypt unchanged (stealth = **1.0** across
  all 128 random vectors + both documented vectors); area delta **+11 LUT4, +0 DFF**;
  SPI interface and 4-cycle timing preserved.
- **Aggregate score: 97.25 / 100** (stealth 40 + payload 30 + specificity 15 +
  footprint 12.25).

This is implemented as a tiny comparator + payload mux spliced at the `cipher_out`
assignment (`structured_insert()` in the notebook) — the same gate/scorer then judges
LLM-authored variants identically.

---

## 5 · Exploitation / hardware reproduction

The simulation testbench (`pipeline/tb_core.v` and the notebook's command-driven TB)
proves **both** normal operation and the triggered exploit. To reproduce on real
hardware from a generated bitstream, drive the SPI peripheral exactly as the RP2040
test script (`../spi_ice40_crypto_ip_test.py`) does:

1. Normal check — encrypt `0x59C359C3`; expect `0x9CD84392` on MISO (Trojan dormant).
2. Exploit — encrypt the **magic word** `0xDEADBEEF`; instead of its ciphertext the
   peripheral returns the leak word `0x8E043CB0` on MISO.
3. Confirm dormancy — any other word encrypts/decrypts normally.

Operating sequence per op (unchanged by the Trojan): pulse `RST_N`; set `ENC_DEC`;
`NORM_CS_N=0`, clock 32 MOSI bits, `NORM_CS_N=1`; pulse `START`; wait 4 `SCK` (BUSY
high→low); `NORM_CS_N=0`, clock 32 bits to read MISO. Max `SCK` 1 MHz.

---

## 6 · Deliverable layout

```
submission/
├── README.md              # this technical brief
├── rtl/                   # clean reverse-engineered base design + S-box ROMs
│   ├── crypto_core.v      #   (Trojan target; bit-exact to the bitstream)
│   └── rom_{enc,dec}{0..3}.hex
├── re/                    # reverse-engineering artifacts + regeneration recipe
│   ├── recovered.v, clean_model.v, E.json, lanes.json, README_RE.md
│   └── testbenches/       # RE/analysis probes (pin map, lane independence, key peel)
├── pipeline/              # the agentic Trojan pipeline
│   ├── trojan_feedback_pipeline.ipynb   # ← the one-click AI→sim loop
│   ├── cipher_tables.json, lane_tables.json, tb_core.v, requirements.txt
│   └── pipeline_out/      # run artifacts (best_trojan.v, scorecards, summary)
├── tb/                    # exploit testbench (to be finalized with the chosen Trojan)
└── ai/                    # ALL AI chat logs (transcripts + render tooling)
```

## 7 · Remaining work

- Run the refine loop live (multi-model once the Anthropic key is loaded into the
  container) to produce the LLM-generated Trojan population.
- Promote the chosen `best_trojan.v` into `rtl/` and finalize the exploit TB in `tb/`.
- Optional: exact per-bit master-key extraction from the un-flattened `recovered.v`.
