"""SecretSense: offline secret detection with redacted reports."""

from secretsense.scanner.engine import scan_path, scan_text
from secretsense.scanner.history import scan_history

__all__ = ["scan_path", "scan_text", "scan_history"]
__version__ = "0.1.0"
