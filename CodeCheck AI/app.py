
import ast
import json
import os
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from openai import OpenAI

app = FastAPI(
    title="CodeCheck AI",
    description="AI-assisted coding mistake finder",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class AnalyzeRequest(BaseModel):
    code: str = Field(min_length=1, max_length=50000)
    language: str = Field(default="python")


def finding(message, severity="WARNING", line=None):
    return {
        "message": message,
        "severity": severity,
        "line": line,
    }


def analyze_python(code):
    findings = []
    suggested_fix = ""

    try:
        ast.parse(code)
    except SyntaxError as error:
        findings.append(
            finding(error.msg, "ERROR", error.lineno)
        )
        suggested_fix = (
            f"Check syntax near line {error.lineno}. "
            "Review colons, brackets, indentation, and quotes."
        )
        return findings, suggested_fix

    for line_number, line in enumerate(
        code.splitlines(), start=1
    ):
        if "TODO" in line:
            findings.append(
                finding(
                    "TODO comment may indicate unfinished work.",
                    "INFO",
                    line_number,
                )
            )

        if re.search(r"""['"].*['"]\s*\+\s*\d+""", line):
            findings.append(
                finding(
                    "Possible string and number concatenation issue.",
                    "WARNING",
                    line_number,
                )
            )

    if not findings:
        findings.append(
            finding(
                "No basic Python syntax errors detected. "
                "Runtime bugs may still exist.",
                "INFO",
            )
        )

    return findings, suggested_fix


def analyze_javascript(code):
    findings = []

    if code.count("{") != code.count("}"):
        findings.append(
            finding(
                "Possible unmatched curly braces.",
                "ERROR",
            )
        )

    if code.count("(") != code.count(")"):
        findings.append(
            finding(
                "Possible unmatched parentheses.",
                "ERROR",
            )
        )

    if not findings:
        findings.append(
            finding(
                "Basic checks passed. Full syntax validation "
                "is not performed.",
                "INFO",
            )
        )

    return findings, ""


def analyze_html(code):
    findings = []

    if code.count("<") != code.count(">"):
        findings.append(
            finding(
                "Possible unmatched HTML angle brackets.",
                "WARNING",
            )
        )

    if "<html" not in code.lower():
        findings.append(
            finding(
                "No HTML root element detected.",
                "WARNING",
            )
        )

    if not findings:
        findings.append(
            finding("Basic HTML checks passed.", "INFO")
        )

    return findings, ""


def analyze_css(code):
    findings = []

    if code.count("{") != code.count("}"):
        findings.append(
            finding(
                "Possible unmatched CSS braces.",
                "ERROR",
            )
        )

    if not findings:
        findings.append(
            finding("Basic CSS checks passed.", "INFO")
        )

    return findings, ""


def analyze_with_ai(code, language):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None

    try:
        client = OpenAI(api_key=api_key)

        prompt = f"""
Analyze the following {language} code for programming issues.

Return ONLY a valid JSON object with these keys:
- findings: an array of objects with message, severity, line
- suggested_fix: a string
- summary: a short string

Severity must be ERROR, WARNING, or INFO.
Use null for line if the line number is unknown.
Do not claim that code was executed.
If there are no issues, return one INFO finding.

Code:
{code}
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a careful code analyzer. "
                        "Return valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content

        if not content:
            return None

        result = json.loads(content)

        if not isinstance(result.get("findings"), list):
            return None

        return result

    except Exception:
        return None


@app.get("/")
def home():
    index_path = os.path.join(BASE_DIR, "index.html")

    if not os.path.isfile(index_path):
        raise HTTPException(
            status_code=404,
            detail="index.html not found",
        )

    return FileResponse(index_path)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "CodeCheck AI",
        "ai_enabled": bool(os.getenv("OPENAI_API_KEY")),
        "message": (
            "AI is enabled."
            if os.getenv("OPENAI_API_KEY")
            else "AI key is missing; basic analysis is available."
        ),
    }


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    code = request.code
    language = request.language.strip().lower()

    analyzers = {
        "python": analyze_python,
        "javascript": analyze_javascript,
        "html": analyze_html,
        "css": analyze_css,
    }

    ai_result = analyze_with_ai(code, language)

    if ai_result is not None:
        findings = ai_result["findings"]
        suggested_fix = ai_result.get("suggested_fix", "")
        summary = ai_result.get(
            "summary",
            "AI analysis completed.",
        )
        ai_enabled = True

    else:
        analyzer = analyzers.get(language)

        if analyzer is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported language. Choose Python, "
                    "JavaScript, HTML, or CSS."
                ),
            )

        findings, suggested_fix = analyzer(code)
        summary = (
            f"Basic analysis completed with "
            f"{len(findings)} finding(s). "
            "Runtime bugs may still exist."
        )
        ai_enabled = False

    has_errors = any(
        item.get("severity") == "ERROR"
        for item in findings
    )

    return {
        "language": language,
        "status": "ISSUES FOUND" if has_errors else "ANALYZED",
        "summary": summary,
        "findings": findings,
        "suggested_fix": (
            suggested_fix
            or "Review each finding and test the code before using it."
        ),
        "ai_enabled": ai_enabled,
    }
