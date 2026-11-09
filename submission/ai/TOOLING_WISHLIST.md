# llm4eda image wishlist (csaw challenge, updated 2026-11-09)

The RE/sim/formal toolchain (yosys, iverilog, IceStorm, Verilator, sby) is complete
and verified working on the real bitstream.

## Python packages needed by the agentic Trojan pipeline (NOT in the image)

Installed at runtime this session (go to `~/.local` or the conda env, so they are
LOST on `llm4eda down`). Bake these into the image for reproducibility. Full pinned
list in `submission/pipeline/requirements.txt`.

| Package | Version | Why |
|---|---|---|
| `pyslang` | 12.1.0 | Verilog/SV AST parse + rewrite (programmatic Trojan insertion). Pulls `nanobind-backend` 1.0.0 |
| `anthropic` | 2.6.0 | Claude API for the multi-model generator (needs `ANTHROPIC_API_KEY`) |
| `openai` | 3.19.2 | OpenAI API for the multi-model generator (needs `OPENAI_API_KEY`) |

Transitive (pip resolves these): httpx2 2.13.1, jiter 0.17.0, pydantic 2.13.5,
anyio 4.15.1, sniffio 1.3.1, typing_extensions 4.16.0, docstring_parser 0.18.0,
opentelemetry-api 1.45.2.

Also set `ANTHROPIC_API_KEY` in `~/.config/llm4eda/env` (OPENAI_API_KEY already present).

## RESOLVED 2026-11-06 — baked into image `llm4eda-lab:2026-11-06.2`

The agentic-Trojan-pipeline Python packages are now in the image (no runtime `pip install` needed). Done in the
llm4eda-lab-docker repo (`recipes/locked/2026-11-06.2/`), committed on branch `x86_port` (not pushed):

- `pyslang` 12.1.0 and `nanobind-backend` 1.0.0 — **note:** the API is in submodules, not the top level:
  `from pyslang.syntax import SyntaxTree` and `from pyslang.ast import Compilation` (not `pyslang.SyntaxTree`).
- `anthropic` 2.6.0 (+ its deps `docstring-parser` 0.18.0, `opentelemetry-api` 1.45.2).
- `openai` 3.19.2 was already in the image at the requested version; the other transitive deps you listed
  (`httpx2`, `jiter`, `pydantic`, `anyio`, `sniffio`, `typing_extensions`) were already present too.

All hash-pinned; `pip check` is clean. Verify in a fresh container:
`python -c "import pyslang, anthropic, openai; print(pyslang.__version__, anthropic.__version__, openai.__version__)"`
or `lab-smoke-test` (check `trojan-pkgs`). See `guide.md` → "SystemVerilog parsing and rewriting: pyslang".

**You must still set `ANTHROPIC_API_KEY`** in `~/.config/llm4eda/env` (mode 600, next to `OPENAI_API_KEY`) — the image
cannot carry secrets. After editing that file, `llm4eda down && llm4eda up ...` to pick it up.

`sv2v` and `pyspice` were not added (sv2v: x86-64-only upstream binary; `yosys -m slang` converts SV→Verilog meanwhile).

## TrojanGYM GNN detector deps (NEW 2026-11-09 — needed by the stealth-scoring gate)

The feedback pipeline now scores each Trojan candidate against the TrojanGYM
Robust-GNN4TJ detector (`submission/pipeline/trojangym_scorer.py` + the "5b GNN gate"
cell in `trojan_feedback_pipeline.ipynb`). The gate degrades gracefully if these are
absent, but without them the learned-stealth score is unavailable. Installed at
runtime this session (ephemeral → lost on `llm4eda down`); bake into the image for
reproducible scoring. Verified working 2026-11-09 on image `2026-11-06.4`, conda
`research` (py3.13), end-to-end through the notebook.

| Package | Version | Why |
|---|---|---|
| `torch-geometric` | **==2.3.1** (PIN) | GNN inference (GCN + SAGPooling). **Must be 2.3.1** — ≥2.4 renamed SAGPooling's internal params (`gnn.lin_rel`/`lin_root` → `select.weight`) and the `model_HT1..4` checkpoints fail to load. `torch` 2.15.0 already in image. |
| `pyverilog` | latest (3.x) | RTL → DFG front-end used by the local `hw2vec`. |
| `pydot` | latest | graph serialization in `hw2graph.py`. |
| `pygraphviz` | latest (2.0.4) | graph build; **C-extension — needs the apt dep below to compile.** |

| apt package | Why |
|---|---|
| `libgraphviz-dev` | build/link headers for `pygraphviz` (the `dot` binary is already in the image, but the dev headers are not — a pip-only install of pygraphviz fails without this). |

Notes:
- A pip-only notebook bootstrap cell is NOT sufficient: `pygraphviz` needs
  `sudo apt-get install -y libgraphviz-dev` first (network + sudo + ~1–2 min build).
- Exact PyVerilog DFG extraction fails on `crypto_core` (`` `default_nettype none ``),
  so `hw2vec` falls back to its heuristic DFG — the same path TrojanGYM uses for AES.
  This is expected; the detector still runs and discriminates.
- The TrojanGYM assets themselves (local `hw2vec/`, `dfg_tj_rtl.pkl`, `model_HT1..4/`)
  live under `TrojanGYM/` in the project folder and persist — only the Python/apt deps
  need baking.

Smoke test in a fresh container:
`cd submission/pipeline && python -c "import trojangym_scorer as t; print(t.score_rtl_text(open('../rtl/crypto_core.v').read())['verdict'])"`
→ expect `CLEAN`.

## EDA extras (lower priority)

| Want | Why | Source | Status |
|---|---|---|---|
| `cocotbext-spi` for cocotb 2.x | SPI cocotb TBs | PyPI | RESOLVED this session (cocotb-2-compatible build installed; imports OK) |
| `sv2v` | SV→Verilog if Trojan RTL authored in SV | github.com/zachjs/sv2v | missing (minor; iverilog handles our SV subset) |
| `pyspice` | not needed for this challenge | — | ignore |

Note: runtime `pip install` / `apt-get` do NOT persist across `llm4eda down`
(only the project folder and `~/.claude-state` survive) — bake into a pinned image.
