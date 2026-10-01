"""One disposable scanner process. Only redacted JSON leaves stdout."""

import json
import sys

from secretsense.scanner.engine import ScanReport, scan_text


def main():
    try:
        payload = json.loads(sys.stdin.buffer.read(6_291_456))
        findings = scan_text(payload["content"], "submitted.txt")
        if len(findings) > payload["limit"]:
            result = {"error": "finding-limit"}
        else:
            result = ScanReport(findings=findings, files_scanned=1).to_dict()
            for finding in result["findings"]:
                finding["masked_value"] = "[REDACTED]"
        output = json.dumps(result, ensure_ascii=True).encode()
        if len(output) > 2_097_152:
            output = b'{"error":"report-limit"}'
        sys.stdout.buffer.write(output)
    except Exception:
        sys.stdout.buffer.write(b'{"error":"scan-failed"}')


if __name__ == "__main__":
    main()
