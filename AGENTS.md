# Webex Test Caller — Agent Guide

## Scope and design

This is a local, source-installed reference application for one controlled test
call at a time. It is not a hosted softphone, a load generator, or a BYOVA gateway.
Read `README.md`, `CONTRIBUTING.md`, and `SECURITY.md` before changing behavior.

- `src/webex_test_caller/cli.py`: CLI inputs, configuration precedence, audio
  preparation, and artifact assembly.
- `auth.py`: local OAuth callback, token refresh, and token storage.
- `runner.py` and `state.py`: browser lifecycle, prompt timing, and assertions.
- `plan.py` and `models.py`: versioned JSON plans and validated run data.
- `audio.py` and `artifacts.py`: local speech/WAV preparation and result files.
- `server.py`: loopback-only browser assets, runtime config, and event ingestion.
- `gateway_events.py` and `gateway_tunnel.py`: optional BYOVA evidence and SSM
  forwarding. Ordinary contact-center tests must work without these features.
- `web/src/`: Calling SDK registration, injected media, DTMF, and browser events.
- `tests/`, `web/*.test.mjs`, and `web/src/*.test.ts`: automated checks.
- `config/`: schema and sample plans. `docs/BYOVA.md`: optional gateway scenarios.

Keep test policy in Python and media/SDK operations in the browser. Use the
existing helpers and standard library. Prefer deleting duplication to adding
layers, dependencies, options, or compatibility aliases. Search every caller,
test, schema, and sample before changing a shared contract. Preserve meaningful
errors, cleanup, validation, and evidence when simplifying code.

## Safe test operation

- Require an explicit, authorized test destination. Never place a live call as
  part of unit tests or CI. Use synthetic speech and non-sensitive DTMF digits.
- Keep caller OAuth, answering-agent, and administrator sign-ins in separate
  browser profiles. Use the designated agent profile for agent logins.
- Do not provision users, change queue/flow/transcription settings, grant new
  OAuth access, or make the repository public without user authorization.
- Preserve loopback binding, exact Host/origin checks, event-size limits, token
  redaction, and private/atomic OAuth token storage.
- Read only `WEBEX_TEST_CALLER_*` application settings. Do not restore legacy
  BYOVA environment-variable aliases.
- Never commit `.env`, OAuth tokens, private keys, generated audio, transcripts,
  artifacts, real destinations, tenant identifiers, or private deployment URLs.
  Use reserved example domains and fictional data in source and fixtures.
- Keep the dependency constraints and remaining advisories in `SECURITY.md`
  accurate. Do not suppress advisories or force incompatible SDK dependencies
  just to produce a clean audit. Keep Webex and Calling SDK versions aligned.

## Validation

Activate the project's virtual environment before running Python:

```bash
source .venv/bin/activate
python -m pytest -q
npm --prefix web test
npm --prefix web run build
npm --prefix web audit --audit-level=high
webex-test-caller validate --config config/contact-center.spec.json --list
webex-test-caller validate --config config/gecx-regression.spec.json --list
webex-test-caller validate --config config/local-audio-dtmf.spec.json --list
git diff --check
```

CI runs Python 3.10/3.12 and Node 22, including the high/critical advisory gate.
Add a focused regression test for a behavior or security fix. Do not add tests
that merely repeat the implementation. Keep Node dependency checks separate
from the browser build's polyfills.

SDK, registration, orchestration, and media changes also need an authorized live
call. Report local tests and live verification separately. Outbound RTP counters
prove transmission, not receipt or recognition. A transcript claim needs a
comparison with the answering desktop's transcript; a transfer claim needs the
documented evidence. Keep private evidence ignored locally. Respect the known
limits in the README, including the current 30-second injection wait.

## Delivery and review

Establish the requested stopping point before implementation and retain it
through follow-ups. This repository supports local validation and a PR with CI;
it has no hosted preview or deployment workflow. Honor an explicit direct-push
instruction without inventing a PR requirement. Otherwise, do not infer push,
merge, deployment, or visibility-change authorization from local editing access.

Retain an established Jira association; do not repeat tracking intake for the
same outcome. Follow the user's tracking and permission rules, and avoid putting
private tracking details in public-facing documentation. Before delivery,
review the final diff, address valid findings, run relevant checks, and follow
any authorized push through CI for that exact commit. Report unresolved risks
and anything not verified. Use conventional commit messages.

For long macOS tasks, run `caffeinate -di` in a persistent terminal session and
stop it with Control-C during cleanup.
