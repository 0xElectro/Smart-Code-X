"""
IERA - Intelligent Error & Recommendation Agent (MVP / Rule-based)

Takes outputs from:
- SAA (StaticAnalysisAgent)
- SCAA (SemanticAnalyzer)
- HDVA (Hallucination Detection)

and returns:
- unified summary
- prioritized recommendations (with simple rule-based suggestions)

Later: plug an ML model inside suggest_fix_ml() and call it here.
"""

from typing import List, Dict, Any

# Simple severity ordering for prioritization
SEVERITY_ORDER = {
    "High": 3,
    "Medium": 2,
    "Low": 1
}

# Optional: agent priority (security/semantic > static style)
AGENT_PRIORITY = {
    "SCAA": 3,   # semantic / logical
    "HDVA": 2,   # hallucinations / incomplete
    "SAA": 1     # static / style / complexity
}


# ---------- 1. Normalization helpers ----------

def _normalize_saa_issues(saa_output: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize SAA issues (StaticAnalysisAgent) into unified format.
    saa_output is a list of dicts produced by StaticAnalysisAgent.analyze(file_path)
    """
    normalized = []
    for issue in saa_output:
        normalized.append({
            "source_agent": "SAA",
            "file": issue.get("file"),
            "function": None,  # SAA works mostly at file/line level
            "line": issue.get("line"),
            "issue": issue.get("message"),
            "severity": issue.get("severity", "Low"),
            "extra": {
                "tool": issue.get("tool"),
                "type": issue.get("type"),
                "symbol": issue.get("symbol")
            }
        })
    return normalized


def _normalize_scaa_issues(scaa_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalize SCAA issues (SemanticAnalyzer.analyze_repository output).
    scaa_output: { "agent": "SCAA", "issues": [...], "summary": {...} }
    """
    normalized = []
    for issue in scaa_output.get("issues", []):
        normalized.append({
            "source_agent": "SCAA",
            "file": issue.get("file"),
            "function": issue.get("function"),
            "line": issue.get("line_number"),
            "issue": issue.get("issue"),
            "severity": issue.get("severity", "Medium"),
            "extra": {
                "similarity": issue.get("similarity"),
                "evidence": issue.get("evidence")
            }
        })
    return normalized


def _normalize_hdva_issues(hdva_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Normalize HDVA issues.
    You should adapt this based on how you structure HDVA's final output.

    Ideal HDVA output format:
    {
        "agent": "HDVA",
        "issues": [
            {
                "file": "...",
                "function": "...",
                "line": 10,
                "issue": "Function appears hallucinated",
                "severity": "High",
                "probability": 0.87
            },
            ...
        ]
    }
    """
    normalized = []
    for issue in hdva_output.get("issues", []):
        normalized.append({
            "source_agent": "HDVA",
            "file": issue.get("file"),
            "function": issue.get("function"),
            "line": issue.get("line"),
            "issue": issue.get("issue"),
            "severity": issue.get("severity", "Medium"),
            "extra": {
                "probability": issue.get("probability")
            }
        })
    return normalized


# ---------- 2. Suggestion generator (rule-based MVP) ----------

def suggest_fix_rule_based(issue_text: str, source_agent: str) -> str:
    """
    Very simple rule-based suggestion engine.
    Later: you will replace/augment this with an ML model.
    """
    text = (issue_text or "").lower()

    # Security / semantic issues
    if "base64" in text and "encrypt" in text:
        return "Use real encryption (e.g., AES or Fernet) instead of base64 encoding."

    if "sql injection" in text or "sqli" in text:
        return "Use parameterized queries or ORM methods instead of string concatenation for SQL."

    if "docstring" in text:
        return "Add a clear, concise docstring explaining the function's purpose, parameters, and return value."

    if "function name" in text and "does not match" in text:
        return "Either rename the function to better match its behavior or adjust the implementation to match its name."

    # Hallucination / incomplete code
    if "todo" in text or "placeholder" in text or "pass" in text:
        return "Replace TODO/pass/placeholder code with a real implementation, or remove the function if not needed."

    if "hallucinated" in text:
        return "Review this function carefully. Replace undefined APIs or magic calls with real, tested logic."

    # Static analysis stuff
    if "unused import" in text:
        return "Remove the unused import to keep the codebase clean and avoid confusion."

    if "maintainability index" in text:
        return "Refactor large or complex functions into smaller ones to improve maintainability."

    if "cyclomatic complexity" in text:
        return "Reduce branching (if/else/loops) or split the function into smaller units with single responsibility."

    # Fallback
    if source_agent == "SAA":
        return "Refactor this issue based on static analysis recommendation and follow standard best practices."
    elif source_agent == "SCAA":
        return "Align the function's implementation with its documented intent or update documentation accordingly."
    elif source_agent == "HDVA":
        return "Review this code carefully for AI-generated or placeholder patterns and replace them with real logic."

    return "Review and refactor this part of the code according to best coding and security practices."


# ---------- 3. (Future) ML-based suggestion hook ----------

def suggest_fix_ml(issue_text: str, source_agent: str) -> str:
    """
    Placeholder for ML-based IERA.
    Later you will:
    - load your fine-tuned CodeT5 / T5 model
    - generate recommendation (+ possibly code fix)
    For now, this just calls the rule-based version.
    """
    # TODO: replace this with real ML inference once the model is trained.
    return suggest_fix_rule_based(issue_text, source_agent)


# ---------- 4. Main recommendation generator ----------

def generate_recommendations(
    saa_output: List[Dict[str, Any]],
    scaa_output: Dict[str, Any],
    hdva_output: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main IERA entrypoint.

    Takes outputs from:
      - StaticAnalysisAgent (list of issues)
      - SemanticAnalyzer (dict with 'issues')
      - HDVA agent (dict with 'issues')

    Returns:
      - unified summary + sorted recommendations
    """

    # 1) Normalize all issues
    normalized_saa = _normalize_saa_issues(saa_output or [])
    normalized_scaa = _normalize_scaa_issues(scaa_output or {})
    normalized_hdva = _normalize_hdva_issues(hdva_output or {})

    all_issues = normalized_saa + normalized_scaa + normalized_hdva

    # 2) Compute basic summary
    total_issues = len(all_issues)
    high_count = sum(1 for i in all_issues if i["severity"] == "High")
    med_count = sum(1 for i in all_issues if i["severity"] == "Medium")
    low_count = sum(1 for i in all_issues if i["severity"] == "Low")

    # 3) Sort issues by severity + source agent priority
    def sort_key(issue: Dict[str, Any]):
        sev_score = SEVERITY_ORDER.get(issue["severity"], 1)
        agent_score = AGENT_PRIORITY.get(issue["source_agent"], 0)
        return (-sev_score, -agent_score)

    all_issues_sorted = sorted(all_issues, key=sort_key)

    # 4) Build recommendation list
    recommendations = []
    for issue in all_issues_sorted:
        suggestion = suggest_fix_ml(issue["issue"], issue["source_agent"])

        recommendations.append({
            "priority": issue["severity"],
            "source_agent": issue["source_agent"],
            "file": issue["file"],
            "function": issue.get("function"),
            "line": issue.get("line"),
            "issue": issue["issue"],
            "suggestion": suggestion,
            # "code_fix": "TODO: will be added once ML model generates code"
        })

    # 5) Final IERA output
    return {
        "agent": "IERA",
        "summary": {
            "total_issues": total_issues,
            "high": high_count,
            "medium": med_count,
            "low": low_count
        },
        "recommendations": recommendations
    }


# For quick manual testing
if __name__ == "__main__":
    # Dummy examples to check the flow
    dummy_saa = [
        {
            "tool": "Pylint",
            "file": "app.py",
            "line": 10,
            "type": "Style",
            "message": "Unused import 'os'",
            "symbol": "unused-import",
            "severity": "Low"
        }
    ]

    dummy_scaa = {
        "agent": "SCAA",
        "issues": [
            {
                "file": "auth.py",
                "function": "encrypt_data",
                "issue": "Function name/docstring implies security (encryption/hashing) but implementation uses insecure methods (base64/MD5/SHA1)",
                "severity": "High",
                "similarity": 0.12,
                "evidence": {},
                "line_number": 42
            }
        ],
        "summary": {}
    }

    dummy_hdva = {
        "agent": "HDVA",
        "issues": [
            {
                "file": "main.py",
                "function": "validate_user",
                "line": 25,
                "issue": "Function contains TODO and pass, looks incomplete or hallucinated",
                "severity": "Medium",
                "probability": 0.83
            }
        ],
        "summary": {}
    }

    out = generate_recommendations(dummy_saa, dummy_scaa, dummy_hdva)
    import json
    print(json.dumps(out, indent=2))
