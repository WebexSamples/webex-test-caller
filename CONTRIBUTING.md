# Contributing

This is a Cisco sample application for controlled contact-center tests. The
[Cisco Sample Code License](LICENSE) applies; this sample is not supported by
Cisco TAC. Keep changes focused and include the checks needed to reproduce them.

## Development

Follow the [README setup](README.md#install), activate `.venv`, then run:

```bash
python -m pytest -q
npm --prefix web test
npm --prefix web run build
npm --prefix web audit --audit-level=high
webex-test-caller validate --config config/contact-center.spec.json --list
webex-test-caller validate --config config/gecx-regression.spec.json --list
webex-test-caller validate --config config/local-audio-dtmf.spec.json --list
git diff --check
```

Automated tests use fake credentials and do not place calls. Live checks require
your own authorized test user and destination. Changes to Calling SDK versions,
registration, or injected media need live call validation as well as unit tests;
state clearly which checks you performed.

## Issues and changes

Use this repository's Issues for reproducible non-security bugs and its pull
requests for proposed changes. Include the Python, Node, operating-system, and
application versions, steps to reproduce, expected behavior, and actual behavior.
For a calling issue, explain which stage failed: authorization, registration,
dialing, audio injection, or an assertion. Use synthetic destinations and
sanitized excerpts rather than uploading entire run artifacts.

Never submit `.env` files, access/refresh tokens, OAuth secrets, private keys,
recordings, transcripts, customer details, internal URLs, or deployment IDs.
Use only reserved example domains and clearly fictional data in tests and docs.
Review the full diff and any new binary files before committing. For a secret
scan, Gitleaks supports `gitleaks git . --redact` for repository history. Do not
attach local credential files or unredacted scanner reports to an issue.

Report security concerns using [SECURITY.md](SECURITY.md), not a public issue.
