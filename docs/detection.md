# Detection rules

The initial engine uses format matching plus Shannon entropy. It never connects
to providers, decodes a credential for validation, or assigns an ML probability.

| Service | Rule ID | Covered shape |
| --- | --- | --- |
| AWS | `aws-access-key` | AKIA/ASIA access key IDs |
| GitHub | `github-token` | Classic and fine-grained prefixed tokens |
| GitLab | `gitlab-token` | glpat personal tokens |
| Stripe | `stripe-key` | Live/test secret and restricted keys |
| Slack | `slack-token` | Common xox-prefixed token variants |
| Google | `google-api-key` | AIza-prefixed API keys |
| SendGrid | `sendgrid-key` | SG-prefixed API keys |
| npm | `npm-token` | npm-prefixed access tokens |
| PyPI | `pypi-token` | pypi-prefixed API tokens |
| Shopify | `shopify-token` | Common shp-prefixed token variants |
| DigitalOcean | `digitalocean-token` | dop_v1 personal tokens |
| Grafana | `grafana-token` | glc-prefixed cloud tokens |
| Hugging Face | `huggingface-token` | hf-prefixed access tokens |
| Docker Hub | `docker-token` | dckr_pat personal tokens |
| Mailgun | `mailgun-key` | Legacy key-prefixed keys |

Additional rules flag JWT-shaped strings and PEM private-key headers. A header
alone is enough for the latter; it does not prove that a complete private key is
present. An AWS access key ID alone is not a usable credential. JWTs can contain
public data. Service formats evolve; these rules cover a subset, not every current
or historical credential format.

The generic rule examines literal assignments to names containing `password`,
`passwd`, `pwd`, `secret`, `token`, `api_key`, or `access_key` (including supported
spelling variants). Values must be 8–256 characters from the supported token
alphabet and have entropy of at least 3.5 bits per character. Variable-name matching
allows at most 80 characters before and after the secret-related keyword to bound
regex work on unusually long input. Common placeholders and environment references
are excluded. Service matches suppress overlapping
generic matches. Low-entropy passwords, escaped strings, multiline literals,
encoded secrets, and credentials outside these patterns may be missed.

Private-key headers have `critical` severity; provider patterns and JWTs have
`high`; generic assignments have `medium`. These labels are review priorities,
not verified impact or confidence scores. Test-mode keys are deliberately flagged.

Pattern design was cross-checked against the public
[Gitleaks rule catalog](https://github.com/gitleaks/gitleaks/blob/master/config/gitleaks.toml).
This is an independent, deliberately smaller implementation, not equivalent coverage.
