# CSAW Hardware Trojan Challenge — Session Handoff Reference

> Purpose: get a fresh Claude session up to speed with **zero prior context**.
> This is a **sanctioned CSAW CTF competition** task: build an AI-generated
> hardware Trojan for a simulated FPGA crypto accelerator. All hardware must be
> AI-written (verified via AI logs). Legitimate security-research / educational context.

Working dir: `/home/researcher/work/csaw` (NOT a git repo). Only the project
folder + Claude state persist; the container is ephemeral.

---

## 1. Access boundary (IMPORTANT — verified 2026-11-06)

The README allows LLMs/teams **only three inputs**. The **source RTL is
deliberately withheld** — it MUST be reverse-engineered from the bitstream.
Do not request, expect, or accept source Verilog for the baseline design.

Files present (all permitted, nothing extra):
- `README.md` — challenge brief, deliverables, scoring rubric.
- `ice40_cryptographic_IP.md` — FPGA interface documentation.
- `spi_ice40_crypto_ip_test.py` — RP2040 MicroPython application/test code.
- `ice40_bitstream.bin` — the FPGA bitstream (104 KB), the RE target.

Verified: no `.v`/`.sv`/netlist files; bitstream begins with iCE40 preamble
`FF 00 00 FF`; no RTL/key strings embedded; no key file present.
If a future session finds source RTL or a key file appearing here, STOP and
flag it to the user — that would be disallowed extra context.

---

## 2. The target (from README + interface doc)

- **Device:** Lattice iCE40 UltraPlus **UP5K** FPGA on the "Hackster" board.
- **Role:** FPGA = SPI **peripheral**; RP2040 = SPI **controller**.
- **Function:** lightweight crypto accelerator. Encrypts/decrypts a **32-bit**
  word. `ENC_DEC`: 0=encrypt, 1=decrypt.
- **Clocking (unusual):** unified clock domain — the SPI `SCK` directly drives
  the shift registers AND the crypto engine. Max **1 MHz** SCK.
- **Latency:** processing takes **4 clock cycles** (BUSY high → low).

### Port map (interface doc §3)
| Pin | Dir | Role |
|---|---|---|
| `SCK` | in | unified system + SPI clock (≤1 MHz) |
| `RST_N` | in | synchronous active-low reset |
| `MOSI` | in | serial data in |
| `MISO` | out | serial data out |
| `NORM_CS_N` | in | active-low CS; acts as shift-enable for input buffer |
| `START` | in | starts encrypt/decrypt |
| `ENC_DEC` | in | 0=encrypt, 1=decrypt |
| `BUSY` | out | high while processing |
| `ICE_LED` | out | mirror of BUSY to onboard LED |

### Operating sequence (interface doc §4)
1. **Init:** pulse `RST_N` low ≥1 cycle, then high; `NORM_CS_N`=1, `START`=0.
2. **Ingest:** set `ENC_DEC`; `NORM_CS_N`=0; clock 32 bits on MOSI; `NORM_CS_N`=1 to latch.
3. **Execute:** pulse `START` high ≥1 SCK, then low; BUSY goes high; ~4 cycles; on BUSY
   falling edge the core parallel-loads the result into the SPI shift register.
4. **Extract:** `NORM_CS_N`=0; 32 SCK cycles → result on MISO; `NORM_CS_N`=1.

### RP2040 pin assignments (from MicroPython test)
`ice_done=GP3`, `SCK=GP6`, `RST_N=GP7`, `MOSI=GP8`, `MISO=GP9`,
`NORM_CS_N=GP10`, `START=GP12`, `ENC_DEC=GP13`, `BUSY=GP14`.
SoftSPI: baud 50 kHz, polarity 0, phase 0, MSB-first, 8-bit.

### Known test vector (fair game — no key leak)
- Encrypt: plaintext `0x59 C3 59 C3` → ciphertext `0x9C D8 43 92`.
- Decrypt: the reverse. Use these to validate a recovered design.
- Note the repeating `59 C3` pattern in plaintext → distinct output words,
  a useful clue about the cipher structure during RE.

---

## 3. The challenge objective

Insert a **stealthy hardware Trojan** into the **reverse-engineered RTL**:
- **Trigger:** specific hidden sequence/data that activates it.
- **Payload:** e.g. leak the key over MISO, silently weaken encryption, or
  predictably corrupt ciphertext.
- Normal operation must be **perfectly preserved** when not triggered.
- **All hardware must be AI-written** (confirmed via submitted AI logs). RTL may
  be renamed/restructured/modularized freely.

### Deliverables (zip)
```
submission.zip
├── README.md (or pdf)   # technical brief
├── rtl/   <modified RTL with Trojan>
├── tb/    <exploit testbench, may build on the MicroPython script>
└── ai/    <ALL AI chat logs — missing logs = disqualification>
```
Technical brief must cover: RE method; AI method (interface/model/framework —
heavily judged for creativity); Trojan trigger+payload+stealth; enough exploit
detail to reproduce in hardware from generated bitstream; proposed explanation
of how the encryption works.

### Scoring weights
- Creative AI use: 35 (AST manipulation / agentic / RAG > plain prompting)
- Trojan quality: 25 (stealth, specific trigger, small footprint, precise payload)
- System automation: 15 (one-click AI→sim pipeline)
- Documentation/reproducibility: 15
- Exploitation simulation: 10 (testbench proves BOTH normal op AND exploit)
- **Bonus +10:** recover the actual encryption key (document how).

---

## 4. Suggested workflow for a new session

1. **Reverse-engineer the bitstream → RTL.** Tooling available in this
   llm4eda-lab container: OSS CAD Suite (`source /opt/oss-cad-suite/environment`)
   — `yosys`, `nextpnr`, **Project IceStorm** (`icebram`, `iceunpack`,
   `icebox_vlog` to turn `.asc`→Verilog), Icarus (`iverilog`/`vvp`, v12 for
   cocotb; `iverilog-13` for suite v13), Verilator, `sby`/solvers. Run
   `lab-info` and read `$LAB_DOCS` for live specifics.
   - Rough path: `iceunpack ice40_bitstream.bin > design.asc` →
     `icebox_vlog design.asc > recovered.v` → clean up / understand →
     simulate against the known test vector to confirm fidelity.
2. **Understand the cipher** (4-cycle, 32-bit, symmetric enc/dec). Identify key
   storage → feeds the +10 bonus and the key-leak payload option.
3. **Design the Trojan with AI** (log everything into `ai/`). Favor a narrow,
   stealthy trigger + precise payload (e.g. key exfil over MISO).
4. **Build exploit testbench** proving normal op + triggered exploit with clear
   waveforms; can adapt `spi_ice40_crypto_ip_test.py` semantics.
5. **Write the technical brief** + assemble the zip in the required layout.

## 4b. Environment setup status (done 2026-11-06)

- **Submission skeleton** created: `submission/{README.md,rtl/,tb/,ai/}`.
- **Toolchain verified working** end-to-end on the real bitstream (iceunpack →
  icebox_vlog). Full RE/sim/formal suite present. Gaps (non-blocking) are logged in
  `submission/ai/TOOLING_WISHLIST.md`: `cocotbext-spi` is incompatible with the lab's
  cocotb 2.1.0, so prefer a **plain-Verilog iverilog testbench** over cocotb for the SPI TB.
- **AI-log persistence SOLVED.** Claude Code writes the full live transcript to
  `~/.claude-state/projects/-home-researcher-work-csaw/<session-id>.jsonl`, and
  `.claude-state` **survives `llm4eda down`** (per `lab-info`) — logs are NOT lost when
  the container/app window closes. For durability + to assemble the deliverable, a copy
  is mirrored into `submission/ai/transcript_<session-id>.jsonl` by
  `submission/ai/snapshot_transcript.sh`.
- **Auto-capture:** a **Stop hook** in `.claude/settings.json` runs that script at the
  end of every turn. NOTE: `.claude/` was created mid-session, so Claude Code's settings
  watcher may not load the hook until the user opens `/hooks` once or restarts the session.
  Until then, run the snapshot script manually. (Each new session: re-run the script to
  capture that session's own `<session-id>.jsonl`; the hook does this automatically.)

## 5. Guardrails
- Keep within the allowed three inputs; flag any unexpected source RTL/key files.
- Never print/commit secrets (API keys are env vars in this lab).
- Container is ephemeral — commit nothing is lost only if in the project folder;
  keep deliverables under `/home/researcher/work/csaw`.
