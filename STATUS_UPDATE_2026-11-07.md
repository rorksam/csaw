# CSAW Challenge — Status Update

## Progress 

Four of five workstreams are done and validated; the live LLM pass and the write-up/packaging are what remain.

### 1. Bitstream → golden model ✅
- **Tools:** OSS CAD Suite — `iceunpack` + `icebox_vlog` (Project IceStorm) to lift the
  104 KB bitstream to a netlist; **Yosys** (`flatten`/`proc`/`memory_collect`/`opt_clean`)
  to rebuild a clean, deterministic Verilog model; **Icarus Verilog** for simulation.
- **Hurdles overcome:**
  - The raw `icebox_vlog` netlist simulated as non-deterministic — the `SB_RAM40_4K`
    read-data register held stale state between operations (RCLKE gating), so the same
    input gave different outputs and the documented test vector wouldn't reproduce.
    Fixed by re-synthesizing through Yosys to behavioral, initialized memories instead
    of hand-patching `cells_sim`.
  - Reproducing the official vector also required matching the driver's **asymmetric
    reset quirk** reverse-engineered from the MicroPython test: encrypt runs with *no*
    reset (it preconditions state via a readback write), decrypt resets first. Once both
    were right, encrypt/decrypt round-trip + 128/128 random vectors matched. Full pin map
    and SPI protocol recovered alongside.

### 2. Cipher break ✅
- **Tools:** targeted Icarus testbenches that sample the BRAM address bundle while
  perturbing one input byte at a time.
- **Hurdles overcome:** proved the design is **4 byte-independent keyed S-box lanes**
  (flipping one input byte moves only the matching output byte), then peeled the rounds.
  The Yosys flatten had merged the pipeline so per-cycle net sampling no longer mapped to
  clean rounds — worked around it by reconstructing the full per-lane substitution tables
  directly (complete functional break) rather than relying on net names.

### 3. Bonus key recovery — ~80% ✅
- Measured per-lane input-whitening from the round-1 BRAM address (affine in the input),
  recovering the high 7 bits of each key byte. Established that only round 1 is
  data-dependent. Remaining gap: the flattened model's byte-select packing breaks affine
  equivalence, so the exact low bit / master key needs the *un-flattened* netlist — a
  clean traceable path for the full +10 if we spend the time.

### 4. AI Trojan pipeline ✅ (the scoring centerpiece)
- **Tools:** a provider-agnostic, **multi-model** loop (Anthropic + OpenAI) in a 21-cell
  notebook — **pyslang** for AST-level parse/rewrite/elaborate (not string splicing),
  **Icarus** for functional sim against a pure-Python golden oracle, **Yosys**
  `synth_ice40 + stat` for the logic-cell footprint metric, plus a custom scorer
  (stealth / payload / specificity / footprint).
- **Hurdles overcome:**
  - `cocotbext-spi` is incompatible with the lab's cocotb 2.1.0 → pivoted to a plain
    command-driven Verilog harness (TB reads a program of R/E/D commands).
  - `yosys -q` silently suppresses the stat table that the footprint metric reads — caught
    and removed.
  - Built an **offline seed bank** so the loop runs end-to-end with no key, which let us
    validate the whole generate→AST-gate→sim→score→refine chain before spending any quota.
  - Reference Trojan (magic-plaintext trigger, leaks over MISO) **scores 97.25**, perfect
    stealth, +11 logic cells.
- Both API keys now confirmed working, so the live multi-model loop is unblocked.

### 5. AI-log capture ✅
- Solved durable transcript capture: a **Stop hook** mirrors each session's live JSONL
  into `submission/ai/`, and `.claude-state` survives `llm4eda down` — so the
  disqualification-risk "missing AI logs" problem is handled automatically.

## What's left ⏳
- **Run the live LLM loop once** (held so far to avoid burning quota without sign-off).
- **Write the technical brief** — `submission/README.md` is still empty; heavily judged.
- **Assemble the final zip:** best Trojan into `rtl/`, exploit TB into `tb/`, AI logs
  already auto-captured.

## One-line summary for the room
> RE, cipher break, and the AI pipeline are built and validated — mostly a story of fighting
> non-deterministic sim, a flattened netlist, and toolchain version mismatches, each worked
> around; the reference Trojan scores 97/100 offline. Left: the live multi-model pass, the
> brief, and packaging.

---
*Saved to the project folder so it survives `llm4eda down`. Companion detail in
`CLAUDE_HANDOFF.md` and per-project memory under `~/.claude-state`.*
