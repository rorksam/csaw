# CSAW Hardware-Trojan Challenge — Technical Brief

> **Status: complete.** Reverse engineering, cipher analysis, and the full agentic
> Trojan-insertion pipeline are built and validated, and the **live multi-model LLM
> pass has been run**. It produced the chosen Trojan **`magic-operand-leak`** (scored
> **100/100**; the LLM output is re-verified bit-exact against the local toolchain in
> `rtl/crypto_core_trojan.v` with the exploit testbench `tb/exploit_tb.v`). The raw
> model responses and run record are in `pipeline/live_run/`. A hand-authored
> **reference Trojan** (`structured_insert`) is retained as the offline validation seed.

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
| **GNN stealth gate** | **TrojanGYM GNN4TJ** (torch-geometric 2.3.1) | 4-model ensemble converts each candidate's RTL to an exact PyVerilog dataflow graph and votes clean/trojan — **self-calibrating** (see §3a): only influences the score when it can actually discriminate on this design family |
| Scorer | all of the above | single weighted scorecard with hard gates (AST / interface / compile / functional) |
| Structured inserter | anchor splice | deterministic AST-located Trojan insertion + offline seed generator |
| Generator | Anthropic / OpenAI | provider-agnostic client; structured JSON candidate contract |
| **Refine loop** | — | feeds each scorecard + simulation diffs back to the model to improve the next candidate; keeps the best |

**Why this scores on "creative AI use":** candidates are gated at the **AST/semantic
level** (pyslang elaboration + port-set equality), not by string matching; generation
is **multi-model**; and the loop is a genuine **feedback/refinement agent** rather than
one-shot prompting. The verification oracle is derived from the *reverse-engineered
cipher itself*, so "normal operation preserved" is checked against the real function.

### 3a · Learned detector gate — and why it *recuses itself* (honest calibration)

A second, **learned** stealth gate layers the four **TrojanGYM Robust-GNN4TJ**
checkpoints on top of the oracle check: each candidate's RTL is converted to an exact
PyVerilog dataflow graph (local `hw2vec`) and the ensemble votes clean/trojan.

The honest finding, and what makes this gate trustworthy: **GNN4TJ is out-of-distribution
for this SPI block cipher.** Measured on the recovered core, the clean base, a small
key-leak, and a *blatant* counter time-bomb all read `P(trojan) ≈ 0.28–0.34` — the
detector cannot see the Trojan here, so an absolute "evades if P < threshold" signal is
meaningless (the blatant Trojan earns it too). On the models' **own labelled dataset**
they do separate strongly (clean median P ≈ 0.25 vs trojan ≈ 0.93), so the failure is
specific to this design family, not a broken detector.

Rather than quietly trust a useless number, the pipeline **calibrates at startup**: it
records the clean-core baseline `P(trojan)`, then runs a deliberately blatant Trojan
control on the same core. The detector only contributes to the score if it separates
that control from clean by ≥ 0.15; otherwise it **sits out** (`evades_detector = None`,
its score weight vanishes) and selection rests on the functional / stealth / specificity
/ footprint gates, which *are* discriminating here. When the detector is informative it
scores the **rise over baseline** (`Δ = P − baseline`), not the raw out-of-distribution
value. This is a deliberate design choice to avoid reporting a fabricated "beats the
detector" result — the kind of over-claim an unaudited learned gate invites.

**Reproducibility:** `pip install -r pipeline/requirements.txt` (pyslang, anthropic,
openai; EDA tools ship in the lab image). Run the notebook top-to-bottom. Setting
`TROJAN_ENABLE_LLM=0` forces the offline seed-bank path for a key-free CI run.
Artifacts land in `pipeline/pipeline_out/` (best RTL, `scorecards.json`, `RUN_SUMMARY.md`);
the committed record of the live LLM pass is under `pipeline/live_run/`.

---

## 4 · Trojan design — the chosen LLM-generated Trojan

The deliverable Trojan, **`magic-operand-leak`**, was authored by the live multi-model
loop (Anthropic `claude-opus-4-8`). It emerged on the loop's third candidate: the first
two (`operand-selftrig-x4`) scored **0** — their self-trigger collided with the
functional test vectors, breaking normal operation — and the refine loop corrected that
into a clean sentinel trigger. RTL: `rtl/crypto_core_trojan.v`; raw model responses and
the run record: `pipeline/live_run/`.

- **Trigger:** a **sentinel operand** (`0xA5A5F00F`) presented to any encrypt *or*
  decrypt operation. It never arises in normal traffic — **false-trigger probability
  ≈ 2⁻³²**; measured false-trigger rate over 128 random vectors = **0**.
- **Payload:** on the trigger the operation returns a **constant leak word
  (`0xDEADC0DE`) on MISO** instead of the true result (a clean core would return
  `0x4F92F627`) — a signalling/exfiltration payload on the observable output. All other
  traffic is bit-exact to the original.
- **Stealth / footprint:** normal encrypt/decrypt unchanged (stealth = **1.0** across
  all 128 random vectors + both documented vectors); area delta **−10 LUT4, +0 DFF**
  (the sentinel mux lets the synthesiser prune the result path, so the Trojan is
  *smaller* than the base); SPI interface and 4-cycle timing preserved.
- **Aggregate score: 100.0 / 100** (stealth 40 + payload 30 + specificity 15 +
  footprint 15), confirmed by an independent re-score on the local toolchain and by the
  self-checking `tb/exploit_tb.v` (all four checks PASS).
- **Learned detector:** GNN4TJ reads it CLEAN (0/4 votes); per §3a the gate is
  out-of-distribution for this family and correctly **recuses itself** rather than
  claiming a stealth result it cannot support.

**Reference / seed Trojan.** The offline `structured_insert()` seed demonstrates the
same flow with a **key-exfiltration** payload: trigger `0xDEADBEEF`, leaking the
recovered key-byte candidates `0x8E043CB0` on MISO (score 97.25, area +11 LUT4). The
identical AST gate + scorer judge the hand-authored seed and the LLM variants the same
way.

---

## 5 · Exploitation / hardware reproduction

The self-checking testbench **`tb/exploit_tb.v`** proves **both** normal operation and
the triggered exploit against `rtl/crypto_core_trojan.v` (all four checks PASS):

```
cd submission/rtl
iverilog -g2012 -o /tmp/exploit.vvp ../tb/exploit_tb.v crypto_core_trojan.v && vvp /tmp/exploit.vvp
```

To reproduce on real hardware from a generated bitstream, drive the SPI peripheral
exactly as the RP2040 test script (`../spi_ice40_crypto_ip_test.py`) does:

1. Normal check — encrypt `0x59C359C3`; expect `0x9CD84392` on MISO (Trojan dormant).
2. Exploit — encrypt the **sentinel word** `0xA5A5F00F`; instead of its ciphertext
   (`0x4F92F627`) the peripheral returns the leak word `0xDEADC0DE` on MISO.
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
│   ├── crypto_core.v         #   clean base (Trojan target; bit-exact to the bitstream)
│   ├── crypto_core_trojan.v  #   ← CHOSEN LLM-generated Trojan (magic-operand-leak)
│   └── rom_{enc,dec}{0..3}.hex
├── re/                    # reverse-engineering artifacts + regeneration recipe
│   ├── recovered.v, clean_model.v, E.json, lanes.json, README_RE.md
│   └── testbenches/       # RE/analysis probes (pin map, lane independence, key peel)
├── pipeline/              # the agentic Trojan pipeline
│   ├── trojan_feedback_pipeline.ipynb   # ← the one-click AI→sim loop
│   ├── trojangym_scorer.py              #   GNN detector gate (see §3a)
│   ├── cipher_tables.json, lane_tables.json, tb_core.v, requirements.txt
│   ├── live_run/          #   committed record of the live LLM pass (summary,
│   │                      #   scorecards, best_trojan.v, raw llm_response_*.txt)
│   └── pipeline_out/      #   ephemeral run artifacts (gitignored; regenerated)
├── tb/                    # exploit testbench
│   └── exploit_tb.v       #   self-checking normal-op + exploit demonstration
└── ai/                    # ALL AI chat logs (transcripts + render tooling)
```

## 7 · Status of remaining work

- ✅ **Live LLM pass run** — the multi-model loop produced the chosen Trojan
  `magic-operand-leak` (`pipeline/live_run/`).
- ✅ **Chosen Trojan promoted** to `rtl/crypto_core_trojan.v` and the exploit testbench
  finalized at `tb/exploit_tb.v` (re-verified locally; all checks PASS).
- ⏳ **Optional bonus:** exact per-bit master-key extraction from the un-flattened
  `recovered.v` (rounds intact) — ~80% done; high 7 bits of each key byte recovered.
- ⏳ **Known issue:** the footprint metric misparses `yosys synth_ice40; stat` on stock
  Colab (reports wrong cell counts); it is correct in the lab image. Scores quoted here
  are the lab-image/local values. Pin or robustify the parser for Colab reproducibility.
