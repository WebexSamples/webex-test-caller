# Webex Test Caller

Dial and test contact centers using the browser Webex Calling SDK. A local Python
CLI owns OAuth, Chromium, caller audio, DTMF, assertions, and run artifacts. No
BYOVA gateway checkout or running gateway is required for ordinary calling tests.

This is a source-installed reference application for controlled test calls. It
uses a licensed Webex Calling user's line and that user's configured dial plan.
It can dial an internal extension or an E.164 number reachable by that line.
Use destinations you are authorized to test; normal Calling/PSTN charges may
apply. Review the [security notes and dependency advisories](SECURITY.md) before use.

## Prerequisites

- **Webex Calling organization and test user:** an organization licensed for Webex
  Calling, with a dedicated Calling user provisioned with a location, extension,
  and a working browser/soft-client registration. A free Webex account alone is
  insufficient. See the official
  [Calling authorization and registration guide](https://developer.webex.com/calling/docs/sdks/webex-calling-sdk-authorization-device-registration).
- **Contact-center destination:** a test entry point reachable through that user's
  dial plan, using an internal extension or E.164 number. Confirm the intended
  IVR/agent flow answers a manual call first. Webex Contact Center tests require
  its entry point and flow to be configured; a BYOVA gateway is needed only for
  the optional BYOVA-specific scenarios.
- **Webex OAuth integration:** a client ID and secret, redirect URI
  `http://localhost:8765/oauth/callback`, and the Calling scopes listed below.
  Authorize it as the dedicated test user.
- **Local tools:** Python 3.10+, Node.js 20.19+ or 22.12+, npm, and Playwright's
  Chromium browser (installed in the setup steps). The SDK runs in Chromium;
  Node is used to build its browser client. The machine needs network access to
  Webex authentication, Calling signaling, and media services.
- **Text-to-speech for text tests:** macOS with the built-in `say` command and an
  installed voice. The default is `Samantha`; list installed voices with
  `say -v '?'` and select another with `--voice`. Check synthesis locally with
  `say -v Samantha 'This is a test.'`. No cloud TTS account or API key is used.
  On other platforms, supply a WAV generated with your own TTS/recording tool
  using `--wav` or a plan's `play` action. DTMF-only plans require no TTS.

## Install

```bash
git clone https://github.com/WebexSamples/webex-test-caller.git
cd webex-test-caller
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python -m playwright install chromium
npm --prefix web ci
cp .env.example .env
chmod 600 .env
```

Keep this source checkout: editable installation and the browser build use its
`web/` directory. The runner rebuilds the client before each call.

## Configure the caller

1. Use a dedicated Webex Calling test user with a Calling location, extension,
   browser/WebRTC calling entitlement, and a working soft-client registration.
2. Verify that user's dial plan routes the chosen extension or number to your
   contact-center entry point. Dial it manually first and confirm the intended
   flow answers. The application does not provision users or contact-center routes.
3. Create a Webex OAuth **Integration** named `Webex Test Caller` with redirect
   URI `http://localhost:8765/oauth/callback` and these scopes:

   ```text
   spark:xsi
   spark:calls_write
   spark:calls_read
   spark:webrtc_calling
   ```

4. Put the integration's client ID and secret into the ignored `.env` file as
   `WEBEX_TEST_CALLER_CLIENT_ID` and `WEBEX_TEST_CALLER_CLIENT_SECRET`. Set
   `WEBEX_TEST_CALLER_TEST_USER_EMAIL` to the dedicated caller's email.
5. Authorize as that caller, using the URL printed by:

   ```bash
   webex-test-caller login
   ```

Use separate browser profiles for the OAuth caller, contact-center answering
agent, and organization administrator. Signing out of one Webex application can
affect other sessions in the same profile. No particular profile name is required.

The user who grants OAuth consent determines the Calling line. The email setting
is a login hint and operator reminder, not an identity assertion. The callback
URI must exactly match the integration. An SDK “unable to find your device” error
usually requires fixing that user's Calling soft-client registration.

## Dial and test

Activate `.venv` in each terminal. Set `TEST_DESTINATION` to your approved test
extension or E.164 number; every run requires an explicit destination.

```bash
export TEST_DESTINATION=1234 # Replace with your configured test destination.

# macOS: render caller speech locally and require a completed remote reply.
webex-test-caller run --destination "$TEST_DESTINATION" \
  --text 'Hello, I need help with my account.' --require-remote-response

# Any supported platform: inject your own audio fixture.
webex-test-caller run --destination "$TEST_DESTINATION" \
  --wav /absolute/path/request.wav --require-remote-response

# Validate a plan without logging in or placing a call.
webex-test-caller validate --config config/contact-center.spec.json --list

# Run the plan's speech or DTMF scenario.
webex-test-caller run --destination "$TEST_DESTINATION" \
  --config config/contact-center.spec.json --test request-response
webex-test-caller run --destination "$TEST_DESTINATION" \
  --config config/contact-center.spec.json --test dtmf-menu
```

Adapt the sample words, menu digit, and expectations to the flow being tested.
Calls run headlessly by default; use `--headed` for visible browser debugging.
The default gate waits for remote audio followed by 750 ms of silence. If no
remote audio starts, it injects after 10 seconds; set
`--initial-silence-fallback-seconds 0` to require a prompt. If ringback precedes
the greeting, `--remote-prompt-occurrence 2` waits for the second audio epoch.

If the route plays continuous audio, opt into a bounded prompt wait:

```bash
webex-test-caller run --destination "$TEST_DESTINATION" \
  --text 'Hello, this is an automated Webex test call.' \
  --max-prompt-wait-seconds 10
```

This sends the first input after a quiet prompt boundary or, at the latest,
10 seconds after media establishment. It can overlap remote audio. The limit
must be positive and less than `--prompt-timeout-seconds`; the overall call
deadline still applies. JSON plans can set `use.maxPromptWaitSeconds`.
This fallback is disabled by default, preserving strict prompt assertions.
The injection event records `max_prompt_wait` when the limit releases speech.

## Test plans and evidence

Version 1 JSON plans contain named tests with alternating actions and expectations.
Use `speak` for macOS text or speech segments with exact pauses, `play` for a WAV
path relative to the plan, and `dtmf` for an IVR digit. Outcomes include
`response`, `response-start`, `session-end`, and `transfer`. Plans can also assert
prompt counts and maximum response latency. See the
[schema](config/webex-test-caller.schema.json) and
[sample plan](config/contact-center.spec.json).

Results in `.artifacts/` record status, timing, destination redaction, input
audio hashes, and browser events. Failed assertions exit nonzero. Artifacts can
still include call, device, or conversation identifiers and diagnostic messages;
review and sanitize them before sharing, even though the run's access token is
redacted from browser diagnostics and events.

Each completed speech injection requires increased outbound RTP packets/bytes
and non-silent source audio energy/duration, recorded in `injection_finished`.
These counters verify transmission by the browser, not recognition or receipt
by a contact-center agent.

To verify speech recognition, answer the test call in your contact-center agent
desktop and compare its live transcript with the fixture's exact spoken text.
Enable transcription for the intended test queue and configure the contact-center
flow according to your provider's instructions. The caller does not enable or
retrieve transcripts. A remote prompt boundary can occur during IVR or queue
audio, before a human answers; allow enough lead-in time in the WAV fixture for
the agent and transcription service to connect.

Remote prompt detection measures audio activity; it does not transcribe or verify what the
contact center said. Transfer assertions without gateway evidence prove only
the configured audio/disconnect sequence, not a successful agent handoff.

BYOVA-specific tests can opt into correlated gateway terminal events and an AWS
SSM tunnel to a private monitoring listener. They are not required for generic
contact-center tests. The existing GECX and Local Audio DTMF plans are retained;
see [BYOVA regression testing](docs/BYOVA.md).

## OAuth storage

The application reads only `WEBEX_TEST_CALLER_*` settings from its local `.env`;
explicit shell values take precedence. Keep that file owner-readable only and
out of Git. Do not commit credentials, generated audio, or artifacts.

`webex-test-caller login` saves tokens with owner-only permissions at
`$XDG_STATE_HOME/webex-test-caller/oauth-token.json` or
`~/.local/state/webex-test-caller/oauth-token.json`. Set
`WEBEX_TEST_CALLER_TOKEN_PATH` to an absolute path to override this location.
Refresh tokens are renewed and saved atomically when the access token expires.
A temporary `WEBEX_TEST_CALLER_ACCESS_TOKEN` can instead authorize a single run
without saving a token. Run `webex-test-caller login` before first use of the
application's token store.

## Validate changes

```bash
source .venv/bin/activate
python -m pytest -q
npm --prefix web test
npm --prefix web run build
npm --prefix web audit --audit-level=high
```

GitHub Actions runs the Python suite on 3.10 and 3.12, builds/tests the browser
client, and rejects high or critical npm advisories. Tests mock speech synthesis
and never authorize or dial a real call.
Live testing requires your configured caller, route, and destination.

The inherited SDK dependency tree has outstanding audit advisories. See
[dependency security status](SECURITY.md) for the dated snapshot.

## Known limits

- Caller audio injection currently has a 30-second event timeout. Keep each
  prepared fixture, including inserted silence, shorter than 30 seconds; the
  overall call deadline also applies.
- Timing is based on media activity, not agent-answer or ASR readiness. A
  completed run does not by itself prove a transcript match or successful transfer.
- This is a local single-caller tool. Do not expose its HTTP listeners, use it
  as a hosted service, or treat it as a load-testing platform.

For development setup, issue reports, and changes, see [Contributing](CONTRIBUTING.md).

## Origin and license

Extracted from `webex/webex-byova-gateway-python` at commit
[`eb2a1e3`](https://github.com/webex/webex-byova-gateway-python/commit/eb2a1e3)
(`tools/byova_e2e/`). The original
[Cisco Sample Code License](LICENSE) is retained. This sample is not supported
by Cisco TAC or tested for production quality or performance.
