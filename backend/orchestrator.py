"""
orchestrator.py

Central controller that runs all agents on a given repository:

- SAA  (StaticAnalysisAgent)         -> static_agent.py
- SCAA (SemanticAnalyzer)            -> semantic_agent.py
- HDVA (Hallucination Detection)     -> hdva_agent.py   (you will expose analyze_hdva())
- IERA (Intelligent Recommender)     -> recommender_agent.py

Usage (for testing):
    python orchestrator.py /path/to/repo
"""

import os
import json
from typing import Dict, Any

# ---- Import your agents ----
from agents.static_agent import StaticAnalysisAgent
from agents.semantic_agent import analyze_semantic
from agents.recommender_agent import generate_recommendations

# ⚠️ Adjust this import based on your file name:
# if your file is agents/hdva_agent.py and you write an analyze_hdva(repo_path) there:
try:
    from agents.hdva_agent import analyze_hdva   # You will implement this wrapper
except ImportError:
    analyze_hdva = None  # fallback, we will handle below


# ---------- Helpers to run each agent safely ----------

def run_saa(repo_path: str):
    """
    Run StaticAnalysisAgent on the repository.
    For now, we call it once with repo_path so tools like bandit/radon
    can run recursively.
    """
    try:
        saa = StaticAnalysisAgent()
        saa_output = saa.analyze(repo_path)   # your analyze() already exists
        return saa_output, None
    except Exception as e:
        return [], f"SAA error: {e}"


def run_scaa(repo_path: str):
    """
    Run Semantic & Contextual Analysis Agent (SCAA).
    """
    try:
        scaa_output = analyze_semantic(repo_path)
        return scaa_output, None
    except Exception as e:
        return {"agent": "SCAA", "issues": [], "summary": {}}, f"SCAA error: {e}"


def run_hdva(repo_path: str):
    """
    Run Hallucination Detection & Validation Agent (HDVA).

    You need to implement an `analyze_hdva(repo_path)` function
    inside your hdva_agent.py that:

    - walks through repo_path
    - finds .py files
    - runs your trained model on each file
    - returns a dict:
        {
          "agent": "HDVA",
          "issues": [
             {
               "file": "...",
               "function": "...",    # optional
               "line": 10,           # optional
               "issue": "Function appears hallucinated",
               "severity": "High",
               "probability": 0.87
             }
          ],
          "summary": {...}
        }
    """
    if analyze_hdva is None:
        # HDVA not wired yet
        return {"agent": "HDVA", "issues": [], "summary": {}}, "HDVA analyze_hdva() not implemented/importable"

    try:
        hdva_output = analyze_hdva(repo_path)
        return hdva_output, None
    except Exception as e:
        return {"agent": "HDVA", "issues": [], "summary": {}}, f"HDVA error: {e}"


# ---------- Main Orchestrator Function ----------

def run_all_agents(repo_path: str) -> Dict[str, Any]:
    """
    High-level function that:
    - Runs SAA, SCAA, HDVA
    - Passes their outputs into IERA
    - Returns final combined JSON
    """

    if not os.path.exists(repo_path):
        return {
            "status": "error",
            "message": f"Repository path does not exist: {repo_path}"
        }

    # 1) Run all analysis agents
    saa_output, saa_err = run_saa(repo_path)
    scaa_output, scaa_err = run_scaa(repo_path)
    hdva_output, hdva_err = run_hdva(repo_path)

    # 2) Run IERA on whatever we got (even if some agents failed)
    iera_output = generate_recommendations(
        saa_output=saa_output,
        scaa_output=scaa_output,
        hdva_output=hdva_output
    )

    # 3) Collect errors (if any)
    errors = []
    if saa_err:
        errors.append(saa_err)
    if scaa_err:
        errors.append(scaa_err)
    if hdva_err:
        errors.append(hdva_err)

    # 4) Final combined structure
    result: Dict[str, Any] = {
        "status": "success" if not errors else "partial_success",
        "agents": {
            "SAA": saa_output,
            "SCAA": scaa_output,
            "HDVA": hdva_output,
            "IERA": iera_output
        }
    }

    if errors:
        result["errors"] = errors

    return result


# ---------- CLI for local testing ----------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py /path/to/repo")
        sys.exit(1)

    repo_path = sys.argv[1]
    output = run_all_agents(repo_path)
    print(json.dumps(output, indent=2, ensure_ascii=False))
