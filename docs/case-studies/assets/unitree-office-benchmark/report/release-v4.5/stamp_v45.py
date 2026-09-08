#!/usr/bin/env python3
"""Stamp a preflight-passed v4.5 candidate without touching scoring data."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.json.read_text(encoding="utf-8"))
    qa = json.loads(args.preflight.read_text(encoding="utf-8"))
    if qa.get("status") != "passed":
        raise SystemExit("preflight QA did not pass")
    entries = report.get("verification", [])
    target = next((row for row in entries if row.get("id") == "verification:v45"), None)
    if target is None:
        raise SystemExit("verification:v45 entry missing")
    target.update({
        "status": "final_offline_qa_passed",
        "passedAt": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "preflightQaSha256": sha256(args.preflight),
        "preflightCheckCount": len(qa.get("checks", [])),
        "preflightFailures": qa.get("failures", []),
        "scope": "JSON引用、分数、排名、血缘、哈希守恒与自包含性；按用户要求未重新打开Word，也未执行新的浏览器效果测试。",
    })
    report["meta"]["status"] = "final_v45_offline_qa_passed"
    report["meta"]["scoringNote"] = str(report["meta"].get("scoringNote", "")).replace("候选版", "正式版")
    for score in report["scores"]["artifacts"].values():
        score["scoreStatus"] = "final_v45_offline_qa_passed"
    for node in report["rankings"].values():
        node["status"] = "final_v45_offline_qa_passed"
        node["isOfficial"] = True
    report["rankingPerspectives"]["status"] = "final_v45_offline_qa_passed"
    report["rankingPerspectives"]["officialResultIds"] = list(report["rankings"])
    report["rankingPerspectives"]["candidateResultIds"] = []
    report["versionHistory"][-1]["status"] = "active_offline_qa_passed"
    report["versionHistory"][-1]["candidateQaSha256"] = sha256(args.preflight)
    report["versionHistory"][-1]["activatedAt"] = target["passedAt"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(args.out), "sha256": sha256(args.out), "status": report["meta"]["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
