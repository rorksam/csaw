# TrojanGYM AES — Course Package

This folder is self-contained for the AES-128 TrojanGYM exercise. Keep the folder
structure unchanged after downloading or extracting it.

## Quick start

1. Use Python 3.10 or 3.11.
2. Install the system tools:
   - macOS: `brew install icarus-verilog graphviz`
   - Ubuntu/Debian: `sudo apt-get install iverilog graphviz libgraphviz-dev pkg-config`
3. From this folder, install Python dependencies:
   `python -m pip install -r requirements.txt`
4. Set `PORTKEY_API_KEY` in the environment, or enter the course key securely when
   the notebook prompts for it.
5. Open `ghost_portkey_trojangym.ipynb`, select the installed Python kernel, and run
   all cells from top to bottom.

The active final cell performs one AES/T1 smoke run: Portkey generation, Verilog
syntax validation, five-vector functional simulation, and four-model GNN detection.
It may use course API quota. Runtime progress and GNN probabilities appear directly
in the notebook.

## Expected outputs

Generated RTL, metadata, and detection reports are written under:

`trojangym_portkey_runs/vulnerable_designs/<model>/aes_128/`

The GNN report includes each HT1–HT4 prediction, `P(clean)`, `P(trojan)`, ensemble
votes, and aggregate Trojan probabilities. AES uses the deterministic heuristic DFG
path because exact PyVerilog expansion is pathological on the large S-box tables.

The four `model_HT1`–`model_HT4` checkpoints are the Robust-GNN4TJ models retrained
for the TrojanGYM work. Their base method comes from GNN4TJ (DATE 2021) and HW2VEC
(HOST 2021). TrojanGYM expands the training set to 884 clean VeriGen RTL designs and
3,536 GHOST/GPT-4 Trojan-infected designs, with one model trained for each HT type.

## Included assets

- `ghost_portkey_trojangym.ipynb`
- `TrojanGYM_Overview_Slides.pptx` (editable 8-slide introduction)
- `TrojanGYM_Overview_Slides.pdf` (ready-to-present/exported copy)
- `2601.17178v3.pdf` (the corresponding TrojanGYM paper)
- AES RTL: `aes_128.v`, `round.v`, and `table.v`
- AES functional testbench
- `dfg_tj_rtl.pkl`
- `model_HT1` through `model_HT4`
- Local patched `hw2vec` source and configuration

The slide deck starts with the one-shot GHOST flow, explains the missing detector
step, and then introduces TrojanGYM's syntax/testbench/detector loop. A dedicated
GNN4TJ page shows the full RTL-to-DFG path, the separate HT1–HT4 trained models,
their probabilities and votes, and the final ensemble rule. The last page connects
this flow to the AES course notebook. The deck uses the official NYU Tandon lockup
and lists the authors from the included paper. The final page outlines a student
extension: prepare a labeled RTL dataset, retrain or fine-tune a detector, evaluate
it on unseen designs, and reconnect the new checkpoint to the notebook.

## Troubleshooting

- `iverilog not found`: install Icarus Verilog and restart the kernel.
- API timeout: verify the configuration cell shows `Request timeout: 300s`.
- No cell output: restart the kernel and run all cells again.
- Missing detector assets: ensure the entire folder was downloaded, not only the
  notebook.

Use only for authorized hardware-security education and research.
