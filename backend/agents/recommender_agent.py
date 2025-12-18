"""
IERA - Intelligent Error & Recommendation Agent (Dynamic / ML-Enhanced)

Takes outputs from:
- SAA (StaticAnalysisAgent)
- SCAA (SemanticAnalyzer)
- HDVA (Hallucination Detection)

and returns:
- unified summary
- prioritized recommendations (with ML-based suggestions)
"""

import os
from typing import List, Dict, Any

# --- ML Imports ---
try:
    from transformers import RobertaTokenizer, T5ForConditionalGeneration
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("IERA Warning: 'transformers' not installed. ML features disabled.")

# --- Global Model Cache ---
_ML_MODEL = None
_ML_TOKENIZER = None

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


# --- Model Loader ---
def _load_ml_model():
    """Lazy load the CodeT5 model."""
    global _ML_MODEL, _ML_TOKENIZER
    if not ML_AVAILABLE:
        return
        
    if _ML_MODEL is None:
        print("IERA: Loading CodeT5 model... (this may take a moment)")
        try:
            model_name = "Salesforce/codet5-small"
            _ML_TOKENIZER = RobertaTokenizer.from_pretrained(model_name)
            _ML_MODEL = T5ForConditionalGeneration.from_pretrained(model_name)
            print("IERA: Model loaded successfully.")
        except Exception as e:
            print(f"IERA: Failed to load ML model: {e}")
            _ML_MODEL = "ERROR"


# --- Context Helper ---
def _get_code_context(repo_path: str, file_path: str, line_no: int, context_lines: int = 3) -> str:
    """Reads source code around the issue line."""
    if not repo_path or not file_path or not line_no:
        return ""
    
    full_path = os.path.join(repo_path, file_path)
    if not os.path.exists(full_path):
        return ""

    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        # line_no is 1-based
        idx = line_no - 1
        start = max(0, idx - context_lines)
        end = min(len(lines), idx + 1 + context_lines)
        
        return "".join(lines[start:end])
    except Exception:
        return ""


# ---------- 1. Normalization helpers ----------

def _normalize_saa_issues(saa_output: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize SAA issues into unified format."""
    normalized = []
    for issue in saa_output:
        normalized.append({
            "source_agent": "SAA",
            "file": issue.get("file", "unknown"),
            "line": issue.get("line", 0),
            "issue": issue.get("message", "Unknown SAA issue"),
            "severity": issue.get("severity", "Low").capitalize(),
            "extra": {
                "tool": issue.get("tool"),
                "type": issue.get("type"),
                "symbol": issue.get("symbol")
            }
        })
    return normalized


def _normalize_scaa_issues(scaa_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize SCAA issues into unified format."""
    normalized = []
    for issue in scaa_output.get("issues", []):
        normalized.append({
            "source_agent": "SCAA",
            "file": issue.get("file", "unknown"),
            "line": issue.get("line_number", 0),
            "issue": issue.get("issue", "Unknown SCAA issue"),
            "severity": issue.get("severity", "Medium").capitalize(),
            "extra": {
                "function": issue.get("function"),
                "similarity": issue.get("similarity"),
                "evidence": issue.get("evidence")
            }
        })
    return normalized


def _normalize_hdva_issues(hdva_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize HDVA issues into unified format."""
    normalized = []
    for issue in hdva_output.get("issues", []):
        normalized.append({
            "source_agent": "HDVA",
            "file": issue.get("file", "unknown"),
            "line": issue.get("line", 0),
            "issue": issue.get("issue", "Potential Hallucination"),
            "severity": issue.get("severity", "High").capitalize(),
            "extra": {
                "function": issue.get("function"),
                "probability": issue.get("probability")
            }
        })
    return normalized


# ---------- 2. Suggestion Generators ----------

def suggest_fix_rule_based(issue_text: str, source_agent: str = "Unknown") -> str:
    """Rule-based suggestion engine (fallback)."""
    text = (issue_text or "").lower()

    # Security / semantic issues
    if "base64" in text and "encrypt" in text:
        return "Use a proper encryption library like 'cryptography' instead of base64 encoding."
    
    if "sql injection" in text or "sqli" in text:
        return "Use parameterized queries (e.g., 'cursor.execute(sql, (val,))') to prevent SQL injection."
    
    if "docstring" in text:
        return "Add a docstring explaining the function's purpose, arguments, and return value."
    
    if "function name" in text and "does not match" in text:
        return "Rename the function to reflect its actual behavior described in the docstring."

    # Hallucination / incomplete code
    if "todo" in text or "placeholder" in text or "pass" in text:
        return "Implement the actual logic for this function. Do not leave it empty."
    
    if "hallucinated" in text:
        return "Verify if this function is actually needed or imported correctly. It appears to be hallucinated."

    # Static analysis stuff
    if "unused import" in text:
        return "Remove this unused import to keep the code clean."
    
    if "maintainability index" in text:
        return "Refactor this code block to reduce complexity (split into smaller functions)."
    
    if "cyclomatic complexity" in text:
        return "Simplify the logic. Too many nested if/else statements."

    # Fallback
    return "Review and refactor this part of the code according to best coding and security practices."


def suggest_fix_ml(issue_text: str, code_context: str) -> str:
    """Dynamic ML-based suggestion using CodeT5."""
    _load_ml_model()
    
    # Fallback if model failed or no context
    if _ML_MODEL is None or _ML_MODEL == "ERROR" or not code_context:
        return suggest_fix_rule_based(issue_text)

    try:
        # Prepare prompt for CodeT5
        input_text = f"# Fix issue: {issue_text}\n{code_context}"
        input_ids = _ML_TOKENIZER(input_text, return_tensors="pt", max_length=512, truncation=True).input_ids
        
        # Generate suggestion
        outputs = _ML_MODEL.generate(input_ids, max_length=128, num_beams=5, early_stopping=True)
        suggestion = _ML_TOKENIZER.decode(outputs[0], skip_special_tokens=True)
        
        return suggestion if suggestion.strip() else suggest_fix_rule_based(issue_text)
        
    except Exception as e:
        print(f"IERA ML Error: {e}")
        return suggest_fix_rule_based(issue_text)


# ---------- 3. Main Recommendation Generator ----------

def generate_recommendations(
    repo_path: str,
    saa_output: List[Dict[str, Any]],
    scaa_output: Dict[str, Any],
    hdva_output: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main IERA entrypoint. Aggregates all agent outputs and generates recommendations.
    """
    
    # 1. Normalize all issues
    all_issues = []
    all_issues.extend(_normalize_saa_issues(saa_output or []))
    all_issues.extend(_normalize_scaa_issues(scaa_output or {}))
    all_issues.extend(_normalize_hdva_issues(hdva_output or {}))

    # 2. Sort issues (High severity first, then by Agent priority)
    all_issues.sort(
        key=lambda x: (
            SEVERITY_ORDER.get(x.get("severity", "Low"), 1),
            AGENT_PRIORITY.get(x.get("source_agent", "SAA"), 1)
        ),
        reverse=True
    )

    # 3. Generate Dynamic Suggestions
    recommendations = []
    for issue in all_issues:
        # Extract actual code context
        context = _get_code_context(repo_path, issue.get("file"), issue.get("line"))
        
        # Generate suggestion (ML with rule-based fallback)
        suggestion = suggest_fix_ml(issue.get("issue"), context)
        
        recommendations.append({
            "priority": issue["severity"],
            "source_agent": issue["source_agent"],
            "file": issue["file"],
            "line": issue.get("line"),
            "issue": issue["issue"],
            "suggestion": suggestion,
            "code_context": context.strip() if context else None,
            "extra": issue.get("extra", {})
        })

    # 4. Summary
    summary = {
        "total_issues": len(recommendations),
        "high": sum(1 for i in recommendations if i["priority"] == "High"),
        "medium": sum(1 for i in recommendations if i["priority"] == "Medium"),
        "low": sum(1 for i in recommendations if i["priority"] == "Low")
    }

    return {
        "agent": "IERA",
        "summary": summary,
        "recommendations": recommendations
    }


# ---------- CLI for Testing ----------

if __name__ == "__main__":
    # Dummy test data
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

    # Test with current directory as repo_path
    out = generate_recommendations(".", dummy_saa, dummy_scaa, dummy_hdva)
    
    import json
    print(json.dumps(out, indent=2))