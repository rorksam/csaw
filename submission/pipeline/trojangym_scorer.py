"""TrojanGYM GNN detector, wrapped as a stealth scorer for the feedback pipeline.

Loads the four per-HT Robust-GNN4TJ checkpoints from the TrojanGYM course package,
converts a Verilog design to a DFG via the local (patched) hw2vec, and runs the
ensemble. `score_rtl_text()` is the convenience entry point used by the notebook.

Design notes / gotchas (verified 2026-11-09):
  * torch-geometric MUST be 2.3.1. Newer tg (>=2.4) renamed SAGPooling's internal
    params (gnn.lin_rel/lin_root -> select.weight) and the checkpoints won't load.
  * Needs: pyverilog, pydot, pygraphviz (+ system libgraphviz-dev), graphviz `dot`.
  * Exact PyVerilog DFG fails on crypto_core (`default_nettype none`); hw2graph then
    falls back to its deterministic heuristic DFG. That is the same path TrojanGYM
    uses for AES, so it is canonical, but it limits the detector's sensitivity to
    this design family. A CLEAN verdict is a stealth signal, not a proof.

Raises DetectorUnavailable when deps or assets are missing, so callers can degrade
gracefully (the pipeline stays runnable without the GNN stack installed).
"""
from __future__ import annotations
import json, os, re, shutil, sys, tempfile
from pathlib import Path


class DetectorUnavailable(RuntimeError):
    """Raised when GNN deps or TrojanGYM assets are not available."""


def default_home() -> Path:
    env = os.environ.get("TJGYM_HOME")
    if env:
        return Path(env).resolve()
    # submission/pipeline/trojangym_scorer.py -> repo root -> TrojanGYM
    return (Path(__file__).resolve().parents[2] / "TrojanGYM").resolve()


_DET: dict | None = None  # cached singleton (models + graph tooling)


def _build_detector(home: Path) -> dict:
    hw2vec_dir = Path(os.environ.get("HW2VEC_DIR", home / "hw2vec"))
    data_pkl = Path(os.environ.get("TJGYM_DATA_PKL", home / "dfg_tj_rtl.pkl"))
    yaml_path = Path(os.environ.get("TJGYM_YAML", hw2vec_dir / "examples" / "example_gnn4tj.yaml"))
    model_paths = {f"HT{i}": home / f"model_HT{i}" for i in (1, 2, 3, 4)}

    missing = [str(p) for p in (hw2vec_dir, data_pkl, *model_paths.values()) if not p.exists()]
    if missing:
        raise DetectorUnavailable("TrojanGYM assets missing: " + "; ".join(missing))

    for p in (str(hw2vec_dir), str(hw2vec_dir / "hw2vec")):
        if p not in sys.path:
            sys.path.insert(0, p)
    try:
        import torch
        import torch.nn as nn
        from config import Config
        from hw2graph import HW2GRAPH, DataProcessor, heuristic_dfg_from_code
        from graph2vec.models import GRAPH2VEC, GRAPH_CONV, GRAPH_POOL, GRAPH_READOUT
        from torch_geometric.loader import DataLoader
    except Exception as e:  # noqa: BLE001
        raise DetectorUnavailable(f"GNN dependency import failed: {e}") from e

    cfg = Config(["--yaml_path", str(yaml_path), "--data_pkl_path", str(data_pkl),
                  "--graph_type", "DFG", "--model_path", ""])
    data_proc = DataProcessor(cfg)
    data_proc.read_graph_data_from_cache(cfg.data_pkl_path)
    hw2graph = HW2GRAPH(cfg)

    models = {}
    for name, path in model_paths.items():
        model = GRAPH2VEC(cfg)
        mcfg = json.load(open(path / "model.cfg"))
        model.set_graph_conv([GRAPH_CONV(*c) for c in mcfg["convs"]])
        model.set_graph_pool(GRAPH_POOL(*mcfg["pool"]))
        model.set_graph_readout(GRAPH_READOUT(mcfg["readout"]))
        model.set_output_layer(nn.Linear(*mcfg["fc"]))
        model.load_state_dict(torch.load(str(path / "model.pth"), map_location="cpu"))
        model.to(cfg.device).eval()
        models[name] = model
    if not models:
        raise DetectorUnavailable("No per-HT models could be loaded.")
    return dict(torch=torch, nn=nn, cfg=cfg, hw2graph=hw2graph, data_proc=data_proc,
                models=models, DataLoader=DataLoader, heuristic=heuristic_dfg_from_code)


def get_detector(home: Path | None = None) -> dict:
    global _DET
    if _DET is None:
        _DET = _build_detector(home or default_home())
    return _DET


def _design_to_loader(det: dict, verilog_file: Path, work_dir: Path, base_dir: Path):
    tmp = work_dir / "hw2vec_test_design"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    inc_pat = r'^\s*`include\s+"[^"]+"\s*$'
    src = verilog_file.resolve()
    (tmp / src.name).write_text(re.sub(inc_pat, "", src.read_text(errors="replace"), flags=re.MULTILINE))
    pending, copied = [src], {src.name}
    while pending:
        cur = pending.pop()
        for inc in re.findall(r'`include\s+"([^"]+)"', cur.read_text(errors="replace")):
            base = Path(inc).name
            if base in copied:
                continue
            cands = [cur.parent / inc, src.parent / inc] + list(base_dir.rglob(base))
            dep = next((p for p in cands if p.is_file()), None)
            if dep is None:
                raise DetectorUnavailable(f"Missing `include '{inc}'")
            dst = tmp / inc
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(re.sub(inc_pat, "", dep.read_text(errors="replace"), flags=re.MULTILINE))
            copied.add(base)
            pending.append(dep)

    srcs = list(tmp.glob("*.v"))
    lookup = sum(len(re.findall(r"(?im)^\s*8'h[0-9a-f]{2}\s*:", p.read_text(errors="replace"))) for p in srcs)
    force_exact = os.environ.get("TJGYM_FORCE_EXACT_DFG", "0") == "1"
    if lookup >= 128 and not force_exact:
        code_path = det["hw2graph"].preprocess(tmp)
        code = Path(code_path).read_text(errors="replace")
        graph = det["heuristic"](code, name="snippet", hw_type="DFG")
    else:
        # hw2graph.code2graph internally catches a PyVerilog failure and falls back
        # to its heuristic DFG, so this path is robust to unparseable RTL.
        graph = det["hw2graph"].code2graph(tmp)
    graph.graph["hw_type"] = "Test"
    graph.graph["label"] = 0
    det["data_proc"].process(graph)
    test_data = det["data_proc"].get_graphs()[-1]
    return det["DataLoader"]([test_data], shuffle=False, batch_size=1)


def detect_file(verilog_file, home: Path | None = None, work_dir: Path | None = None) -> dict:
    """Run the 4-model ensemble on a .v file. Returns per-model + ensemble probs."""
    import torch.nn.functional as F
    det = get_detector(home)
    vfile = Path(verilog_file).resolve()
    work = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix="tjgym_"))
    work.mkdir(parents=True, exist_ok=True)
    loader = _design_to_loader(det, vfile, work, vfile.parent)
    results, triggered = {}, []
    for name, model in det["models"].items():
        with det["torch"].no_grad():
            outs = []
            for data in loader:
                data.to(det["cfg"].device)
                emb, _ = model.embed_graph(data.x, data.edge_index, data.batch)
                emb = F.log_softmax(model.mlp(emb), dim=1)
                outs.append(emb.cpu())
            outs = det["torch"].cat(outs).reshape(-1, 2).detach()
            pred = int(outs.max(1)[1].item())
            probs = det["torch"].exp(outs).detach().numpy()[0]
        results[name] = {"prediction": pred, "prob_clean": float(probs[0]),
                         "prob_trojan": float(probs[1])}
        if pred == 1:
            triggered.append(name)
    tp = [m["prob_trojan"] for m in results.values()]
    return {
        "available": True, "file": str(vfile),
        "per_model": results, "triggered": triggered,
        "trojan_votes": len(triggered), "model_count": len(results),
        "mean_prob_trojan": sum(tp) / len(tp) if tp else 0.0,
        "max_prob_trojan": max(tp, default=0.0),
        "min_prob_trojan": min(tp, default=0.0),
        "verdict": "TROJAN" if triggered else "CLEAN",
    }


def score_rtl_text(rtl_text: str, home: Path | None = None, name: str = "cand") -> dict:
    """Write RTL to a temp .v and score it. Used by the notebook's gnn_detect()."""
    work = Path(tempfile.mkdtemp(prefix="tjgym_"))
    vfile = work / f"{re.sub(r'[^A-Za-z0-9_]', '_', name)}.v"
    vfile.write_text(rtl_text)
    return detect_file(vfile, home=home, work_dir=work)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("verilog")
    ap.add_argument("--home", default=None)
    args = ap.parse_args()
    print(json.dumps(detect_file(args.verilog, home=Path(args.home) if args.home else None), indent=2))
