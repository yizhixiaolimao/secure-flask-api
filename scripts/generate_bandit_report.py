import html
import json
import sys
from pathlib import Path

from bandit.core import docs_utils, extension_loader


json_path = Path(sys.argv[1])
html_path = Path(sys.argv[2])

data = json.loads(json_path.read_text(encoding="utf-8"))
manager = extension_loader.MANAGER

# 获取 Bandit 当前安装版本中的所有检查规则
rules = {}

for plugin in manager.plugins:
    test_id = plugin.plugin._test_id
    rules[test_id] = plugin.name

for test_id, rule in manager.blacklist_by_id.items():
    rules[test_id] = rule["name"]

# 按规则整理扫描结果
findings_by_rule = {}

for finding in data.get("results", []):
    test_id = finding["test_id"]
    findings_by_rule.setdefault(test_id, []).append(finding)
    rules.setdefault(test_id, finding.get("test_name", "Unknown rule"))


def rule_sort_key(test_id):
    if test_id.startswith("B") and test_id[1:].isdigit():
        return int(test_id[1:])
    return 999999


rows = []

for test_id in sorted(rules, key=rule_sort_key):
    findings = findings_by_rule.get(test_id, [])
    count = len(findings)

    if count:
        status = '<span class="fail">FAIL — Finding detected</span>'
    else:
        status = '<span class="pass">PASS — No finding</span>'

    documentation = docs_utils.get_url(test_id)

    rows.append(
        f"""
        <tr>
            <td><a href="{html.escape(documentation)}">{test_id}</a></td>
            <td>{html.escape(rules[test_id])}</td>
            <td>{status}</td>
            <td>{count}</td>
        </tr>
        """
    )

details = []

for finding in data.get("results", []):
    cwe = finding.get("issue_cwe") or {}
    cwe_text = (
        f"CWE-{cwe.get('id')}" if cwe.get("id") is not None else "Not specified"
    )

    details.append(
        f"""
        <div class="finding">
            <h3>{html.escape(finding["test_id"])}:
                {html.escape(finding.get("test_name", ""))}
            </h3>
            <p><b>Severity:</b>
                {html.escape(finding.get("issue_severity", ""))}
            </p>
            <p><b>Confidence:</b>
                {html.escape(finding.get("issue_confidence", ""))}
            </p>
            <p><b>CWE:</b> {html.escape(cwe_text)}</p>
            <p><b>File:</b>
                {html.escape(finding.get("filename", ""))}
            </p>
            <p><b>Line:</b>
                {finding.get("line_number", "")}
            </p>
            <p><b>Description:</b>
                {html.escape(finding.get("issue_text", ""))}
            </p>
            <pre>{html.escape(finding.get("code", ""))}</pre>
        </div>
        """
    )

metrics = data.get("metrics", {})
totals = metrics.get("_totals", {})
scanned_files = len([name for name in metrics if name != "_totals"])
total_findings = len(data.get("results", []))
failed_rules = len(findings_by_rule)
passed_rules = len(rules) - failed_rules

report = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Complete Bandit SAST Report</title>
<style>
body {{
    font-family: Arial, sans-serif;
    margin: 30px;
    color: #222;
}}
.summary {{
    background: #f4f6f8;
    border: 1px solid #ccd2d8;
    padding: 16px;
    margin-bottom: 25px;
}}
table {{
    width: 100%;
    border-collapse: collapse;
}}
th, td {{
    border: 1px solid #ccd2d8;
    padding: 9px;
    text-align: left;
}}
th {{
    background: #263238;
    color: white;
}}
.pass {{
    color: #167c3a;
    font-weight: bold;
}}
.fail {{
    color: #c62828;
    font-weight: bold;
}}
.finding {{
    margin-top: 18px;
    padding: 15px;
    border-left: 5px solid #c62828;
    background: #fff3f3;
}}
pre {{
    background: #202124;
    color: #f1f1f1;
    padding: 12px;
    overflow-x: auto;
}}
</style>
</head>
<body>

<h1>Complete Bandit SAST Report</h1>

<div class="summary">
    <p><b>Generated at:</b>
        {html.escape(data.get("generated_at", "Unknown"))}
    </p>
    <p><b>Files scanned:</b> {scanned_files}</p>
    <p><b>Lines of code:</b> {totals.get("loc", 0)}</p>
    <p><b>Total Bandit checks:</b> {len(rules)}</p>
    <p><b>Passed checks:</b> {passed_rules}</p>
    <p><b>Checks with findings:</b> {failed_rules}</p>
    <p><b>Total findings:</b> {total_findings}</p>
    <p><b>Lines suppressed with #nosec:</b>
        {totals.get("nosec", 0)}
    </p>
</div>

<h2>All Bandit Checks</h2>

<table>
<thead>
<tr>
    <th>Rule ID</th>
    <th>Check name</th>
    <th>Result</th>
    <th>Findings</th>
</tr>
</thead>
<tbody>
{"".join(rows)}
</tbody>
</table>

<h2>Finding Details</h2>
{"".join(details) if details else "<p>No security findings detected.</p>"}

</body>
</html>
"""

html_path.write_text(report, encoding="utf-8")