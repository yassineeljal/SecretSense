# Benchmarks

No detection-quality benchmark has been run. Unit-test pass rates are software
validation, not evidence of real-world precision or recall.

The planned comparison includes regex alone, rules plus entropy, a trained local
model, and optional local-LLM assistance. Each run must record the dataset version,
source-grouped split, commit, dependency versions, hardware, runtime, precision,
recall, F1, confusion matrix, and error examples with values removed. Hold out
entire repositories and synthetic template families from training.

Published tables and website charts will be populated from reproducible evaluation
artifacts after dataset and model work is complete.
