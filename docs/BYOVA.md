# BYOVA regression testing

These optional scenarios exercise a BYOVA gateway through a configured Webex
Contact Center flow. Ordinary contact-center calling needs no BYOVA gateway.
First complete the [standalone app setup and caller authorization](../README.md).
Run the following commands from the `webex-test-caller` checkout with its virtual
environment active. Set `TEST_DESTINATION` to your approved test extension or
E.164 entry-point number before running any calling commands.

```bash
export TEST_DESTINATION=1234 # Replace with your configured test entry point.
```

The preserved GECX and Local Audio plans opt into gateway evidence. Configure the
restricted monitoring endpoint or private tunnel described below before running
those plans. Their flow-specific speech and DTMF expectations must match your
selected test flow.

### Run a bounded natural-pause scenario

Use repeated `--text-segment` values to render one deterministic caller WAV
with exact sample-level silence between phrases. The following command inserts
1.8 seconds of silence: one second for the gateway VAD end-silence threshold
and 800 ms inside the default one-second GECX resume grace.

```bash
webex-test-caller run \
  --destination "$TEST_DESTINATION" \
  --text-segment "I'd like to book" \
  --text-segment "a room in San Jose" \
  --segment-pause-ms 1800 \
  --remote-prompt-occurrence 2 \
  --require-remote-response \
  --response-timeout-seconds 30
```

With `--require-remote-response`, the run fails unless remote audio begins
after caller injection and subsequently becomes quiet. The artifact records
the segment count, inserted pause, response observation, and measured response
latency. It also records UTC receipt time for every browser event plus the
overall UTC run window, providing an exact interval for gateway and CES log
correlation. Confirm that both segments formed one CES transcript and one WxCC
START/END boundary pair.

For Webex Contact Center entry points that play ringback before the virtual
agent greeting, `--remote-prompt-occurrence 2` waits for the second completed
remote-audio epoch. This prevents the caller fixture from being injected
between ringback and creation of the BYOVA conversation.

Live runs use headless Chromium by default, so automated calls do not open a
browser window over other work. Add `--headed` only when interactive browser
media debugging is required.

## Define tests in JSON

Each version 1 test contains alternating caller-input actions and expectations. A
`speak` action accepts either `text` or `segments` plus `pauseMs`; a `play`
action accepts a WAV `path` relative to the config file. A `dtmf` action sends
exactly one of `0-9`, `A-D`, `*`, or `#` through the Webex Calling SDK.
`response` waits for a
complete remote prompt. `response-start` waits only until remote audio becomes
active, allowing the next action to exercise caller speech during playback.
`session-end` and `transfer` are terminal expectations and must be the final
step. Test plans follow Playwright conventions: top-level `use` defaults, named
`tests`, ordered `steps`, and explicit `expect` assertions. Reference
`config/webex-test-caller.schema.json` for editor validation and autocomplete.

```json
{
  "$schema": "./webex-test-caller.schema.json",
  "version": 1,
  "use": {
    "headless": true,
    "responseTimeoutSeconds": 30,
    "requireGatewayEvents": true
  },
  "tests": [
    {
      "id": "request-response",
      "title": "receives a complete virtual-agent response",
      "steps": [
        {
          "name": "Speak one request",
          "action": "speak",
          "text": "Please help me with my request."
        },
        {
          "name": "Expect one complete response",
          "expect": {
            "outcome": "response",
            "responsePrompts": 1,
            "maxLatencySeconds": 6.0
          }
        }
      ]
    }
  ]
}
```

DTMF plans do not require a WAV fixture. This example asserts both the
caller-observed prompt and the exact gateway terminal event:

```json
{
  "id": "dtmf-transfer",
  "title": "DTMF 5 transfers the Local Audio call",
  "steps": [
    {"action": "dtmf", "digit": "5"},
    {"expect": {"outcome": "transfer", "responsePrompts": 1}}
  ]
}
```

Use DTMF actions only for non-sensitive test controls. The browser event and
run artifact record only that one digit was sent, not its value. The checked-in
`config/local-audio-dtmf.spec.json` plan covers Local Audio digit 5 transfer and
digit 6 session end. It also requires gateway evidence that the correlated
conversation used the `websocket` transport and agent
`Local Audio: Local Playback`.

A two-turn test uses the same action/expectation rhythm:

```json
{
  "id": "two-turn",
  "title": "continues the conversation for a second caller turn",
  "steps": [
    {"action": "speak", "text": "I need a hotel."},
    {"expect": {"outcome": "response"}},
    {"action": "speak", "text": "A queen room, please."},
    {"expect": {"outcome": "response"}}
  ]
}
```

To inject the second utterance while the first response is playing, replace the
first `response` outcome with `response-start`. The final `response`
expectation observes audio after the second injection. Correlate the provider's
transcript to prove that the virtual agent recognized that utterance.

Validate and list the plan without authenticating or placing a call:

```bash
webex-test-caller validate --config path/to/connector.spec.json --list
```

Then run one selected test with Playwright-style `--config` selection:

```bash
webex-test-caller run \
  --destination "$TEST_DESTINATION" \
  --config path/to/connector.spec.json \
  --test request-response
```

Top-level `use` values apply to every test. A test may define its own `use`
object to override those defaults. Explicit CLI options have final precedence,
which is useful for a one-off timeout or headed debugging run. The loader
rejects unsupported versions, duplicate test IDs, invalid step order, and
unknown fields before it obtains a token or places a call.

`maxLatencySeconds` is an optional per-expectation upper bound from the
preceding `injection_finished` event to the first subsequent
`remote_audio_active` event. A run fails when the measured response-start
latency exceeds that bound. Successful runs retain the observed value in the
step result and run artifact; failed runs include both the observed value and
target in the artifact error.

The completed artifact records the selected test, config path and SHA-256,
expected outcome, completed remote-prompt count, Calling SDK disconnect
cause/code, whether the caller requested that disconnect, the correlated gateway
terminal event, and the exact UTC event window. The config hash ties live
evidence to the exact plan contents.

When `requireGatewayEvents` is enabled, provide the gateway monitoring base URL
or its `/api/connections` endpoint. The runner snapshots existing diagnostic
events before dialing, binds the one new gateway conversation to the run, and
asserts its exact `SESSION_END` or `TRANSFER_TO_AGENT` event. A normal response
fails if either terminal event appears.

```bash
export WEBEX_TEST_CALLER_GATEWAY_EVENTS_URL=http://127.0.0.1:8080
```

`--gateway-events-url` overrides the environment for one run. Keep the
development monitoring interface on a restricted or securely forwarded path;
do not expose it publicly for E2E access.

For an AWS deployment whose monitoring listener is private, the runner can own
an AWS Systems Manager remote-host port-forward for the duration of the call.
This requires AWS CLI credentials, the Session Manager plugin, and an
SSM-managed EC2 instance that can reach the gateway's private host and port.
Supply deployment-specific identifiers through the ignored `.env` file or the
equivalent CLI options; do not put them in a committed test plan.

```bash
export WEBEX_TEST_CALLER_GATEWAY_EVENTS_SSM_TARGET=i-0123456789abcdef0
export WEBEX_TEST_CALLER_GATEWAY_EVENTS_SSM_HOST=10.0.1.25
export WEBEX_TEST_CALLER_GATEWAY_EVENTS_SSM_REGION=us-east-1

webex-test-caller run \
  --destination "$TEST_DESTINATION" \
  --text 'Please transfer me to an agent.' \
  --expect-outcome transfer
```

The runner starts `AWS-StartPortForwardingSessionToRemoteHost` without a shell,
waits for `http://127.0.0.1:18080`, reads `/api/connections` through that
loopback listener, and terminates the session after the run. Override the
private port with `WEBEX_TEST_CALLER_GATEWAY_EVENTS_SSM_REMOTE_PORT` and the loopback
port with `WEBEX_TEST_CALLER_GATEWAY_EVENTS_SSM_LOCAL_PORT`. The corresponding CLI
options use the `--gateway-events-ssm-*` prefix. A direct gateway-events URL and
an SSM tunnel are mutually exclusive.

For custom fixtures, `--expect-outcome response|session-end|transfer` enables
the same assertions without using a named test. Flows that guarantee a
minimum connected interval after transfer can add
`--connected-observation-seconds`; it is disabled by default because queue and
agent-availability behavior differs after WxCC accepts the transfer event.

## Run the GECX regression plan

The application retains `config/gecx-regression.spec.json`. Validate
and inspect it without placing a call:

```bash
webex-test-caller validate --config config/gecx-regression.spec.json --list
```

The plan requires correlated gateway events. Before running it, set either
`WEBEX_TEST_CALLER_GATEWAY_EVENTS_URL` to a restricted monitoring endpoint or configure
the SSM tunnel above for the same gateway deployment being called.

Run one test at a time against the dedicated non-production entry point:

```bash
webex-test-caller run --destination "$TEST_DESTINATION" \
  --config config/gecx-regression.spec.json \
  --test normal-response

webex-test-caller run --destination "$TEST_DESTINATION" \
  --config config/gecx-regression.spec.json \
  --test long-response

webex-test-caller run --destination "$TEST_DESTINATION" \
  --config config/gecx-regression.spec.json \
  --test natural-pause

webex-test-caller run --destination "$TEST_DESTINATION" \
  --config config/gecx-regression.spec.json \
  --test multi-turn-response

webex-test-caller run --destination "$TEST_DESTINATION" \
  --config config/gecx-regression.spec.json \
  --test speak-during-playback

webex-test-caller run --destination "$TEST_DESTINATION" \
  --config config/gecx-regression.spec.json \
  --test task-complete

webex-test-caller run --destination "$TEST_DESTINATION" \
  --config config/gecx-regression.spec.json \
  --test transfer
```

Correlate each artifact window and config SHA-256 with gateway and CES evidence:

- `normal-response`: one caller turn and an explicit assertion that the
  correlated gateway conversation emitted no terminal output event.
  It is also the canonical latency gate. Three runs against deployed commit
  `0bd3be9` on August 5, 2026 measured 5.779, 4.581, and 5.212 seconds from
  caller injection completion to first remote response audio (5.191-second
  mean; 5.779-second maximum). The committed target is at most 6.0 seconds.
  Re-run this named scenario after each runtime or endpointing change and retain
  its config-hashed artifact before closing SE-1943.
- `long-response`: multiple ordered raw audio chunks, first audio before CES
  turn completion, and exactly one normal `FINAL`. It uses a 2.5-second
  remote-silence threshold so a natural pause inside streamed playback is not
  mistaken for the end of the prompt.
- `natural-pause`: one outward `START_OF_INPUT`, one merged resume, one outward
  `END_OF_INPUT`, and one complete CES transcript.
- `multi-turn-response`: two caller injections, two complete GECX responses,
  and no terminal output event. It uses the same 2.5-second streamed-prompt
  completion threshold before injecting turn two.
- `speak-during-playback`: an audio-plane probe. The second caller
  injection begins after the first GECX response starts and the call remains
  healthy through remote-audio completion. Streamed GECX chunks keep barge-in
  disabled until Phase 4, so a green runner result does **not** prove CES
  received the second utterance; correlate the CES transcript and record that
  live semantic gap explicitly.
- `task-complete`: one correlated gateway `SESSION_END` output event before the
  remote disconnect.
- `transfer`: one correlated gateway `TRANSFER_TO_AGENT` output event and the
  configured post-input announcement epochs. Match the count to the selected
  agent and flow; some CES agents escalate without a spoken announcement. A
  normal remote disconnect after the required audio is accepted when no
  connected-observation interval is requested. A normal response, an error
  disconnect, and a transfer required to stay connected still fail on early
  disconnect.

The latency target preserves the current evidence-backed endpointing tradeoff:
gateway end-silence and speech-resume grace remain one second each, while GECX
appends two seconds of codec-correct endpointing silence because one second left
short CES turns open. The `remoteSilenceMs` threshold affects prompt-completion
observation, not response-start latency. Tune it in a private profile for the selected agent: a
short interval can inject during a welcome pause, while a long interval can
overlap an autonomous no-input reprompt. With barge-in disabled, an early
injection can be discarded by WxCC. An autonomous no-input reprompt can then
satisfy an audio-only response expectation: a green caller result alone is not
a speech-recognition pass. Correlate every expected caller turn with provider
recognition evidence before accepting the scenario.

If the selected CES agent starts a no-input reprompt immediately after its
welcome, record whether the caller injection overlaps it. A non-interruptible
reprompt can prevent the complete utterance reaching the gateway. Configure the
existing autonomous-prompt `barge_in_enabled` option only when that behavior is
intended, and retain the configuration fingerprint with the run; greeting and
caller-triggered reply chunks remain non-interruptible.

## Safety boundaries

- The local server listens only on loopback and suppresses HTTP request logs so
  the access token is not printed.
- `run` deliberately dials only the destination passed for that invocation.
- The browser client measures remote audio activity with Web Audio; it does not
  transcribe, store, or upload remote prompt audio.
- This tool records its own timing events and audio hash, not call recordings or
  OAuth tokens.
