"""SecretSense: offline secret detection with redacted reports."""

from secretsense.scanner.engine import scan_path, scan_text

__all__ = ["scan_path", "scan_text"]
__version__ = "0.1.0"
