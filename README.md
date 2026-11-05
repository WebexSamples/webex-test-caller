# Webex Test Caller

Dial and test contact centers using the browser Webex Calling SDK. A local Python
CLI owns OAuth, Chromium, caller audio, DTMF, assertions, and run artifacts. No
BYOVA gateway checkout or running gateway is required for ordinary calling tests.

This is a source-installed reference application for controlled test calls. It
uses a licensed Webex Calling user's line and that user's configured dial plan.
It can dial an internal extension or an E.164 number reachable by that line.

## Install

Use Python 3.10+ and Node.js 20.19+ or 22.12+. Webex Calling runs in Chromium;
Node is only used to build the browser client. Text-to-speech uses the built-in
macOS `say` command. On other platforms, use a WAV fixture or DTMF-only plan.
The automated tests mock speech synthesis and do not place calls.

```bash
git clone https://github.com/WebexSamples/webex-test-caller.git
cd webex-test-caller
python3 -m venv .venv
source .venv/bin/activate
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
   `BYOVA_E2E_WEBEX_CLIENT_ID` and `BYOVA_E2E_WEBEX_CLIENT_SECRET`. Set
   `BYOVA_E2E_TEST_USER_EMAIL` to the dedicated caller's email. The historical
   `BYOVA_E2E_` prefix is retained for compatibility.
5. Authorize as that caller, using the URL printed by:

   ```bash
   webex-test-caller login
   ```

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

## Test plans and evidence

Version 1 JSON plans contain named tests with alternating actions and expectations.
Use `speak` for macOS text or speech segments with exact pauses, `play` for a WAV
path relative to the plan, and `dtmf` for an IVR digit. Outcomes include
`response`, `response-start`, `session-end`, and `transfer`. Plans can also assert
prompt counts and maximum response latency. See the
[schema](config/byova-e2e.schema.json) and
[sample plan](config/contact-center.spec.json).

Results in `.artifacts/` record status, timing, destination redaction, input
audio hashes, and browser events. Failed assertions exit nonzero. Remote prompt
detection measures audio activity; it does not transcribe or verify what the
contact center said. Transfer assertions without gateway evidence prove only
the configured audio/disconnect sequence, not a successful agent handoff.

BYOVA-specific tests can opt into correlated gateway terminal events and an AWS
SSM tunnel to a private monitoring listener. They are not required for generic
contact-center tests. The existing GECX and Local Audio DTMF plans are retained;
see [BYOVA regression testing](docs/BYOVA.md).

## Existing BYOVA caller users

The `byova-e2e` command, Python module `byova_e2e`, environment variable names,
JSON format, and artifact filenames remain compatible. Both commands run the
same application. Existing plan files can be used with an explicit `--config`.

Move your old `tools/byova_e2e/.env` to this checkout's `.env` locally and keep it
owner-readable only. Do not commit credentials, generated audio, or artifacts.
Token storage stays at `$XDG_STATE_HOME/byova-e2e/oauth-token.json` or
`~/.local/state/byova-e2e/oauth-token.json` with owner-only permissions, so a
valid saved login can be reused. If you still have a checkout-local
`.state/oauth-token.json`, copy that `.state/` directory into this checkout
before first use; the existing migration reads it there. Set
`BYOVA_E2E_WEBEX_TOKEN_PATH` to an absolute path to override the shared location.
Refresh tokens are renewed and saved atomically when the access token expires.

## Validate changes

```bash
source .venv/bin/activate
python -m pytest -q
npm --prefix web test
npm --prefix web run build
```

GitHub Actions runs the Python suite on 3.10 and 3.12 and builds/tests the browser
client. These checks never authorize or dial a real call. Live testing requires
your configured caller, route, and destination.

The inherited SDK dependency tree has outstanding audit advisories. See
[dependency security status](SECURITY.md) for the extraction-time snapshot.

## Origin and license

Extracted from `webex/webex-byova-gateway-python` at commit
[`eb2a1e3`](https://github.com/webex/webex-byova-gateway-python/commit/eb2a1e3)
(`tools/byova_e2e/`), tracked under SE-2486. The original
[Cisco Sample Code License](LICENSE) is retained. This sample is not supported
by Cisco TAC or tested for production quality or performance.
