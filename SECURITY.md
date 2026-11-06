# Security

## Reporting a vulnerability

Do not include credentials, private call data, or exploit details in public
issues. Use the reporting instructions in the
[Cisco Security Vulnerability Policy](https://sec.cloudapps.cisco.com/security/center/resources/security_vulnerability_policy.html).
For ordinary bugs, follow [Contributing](CONTRIBUTING.md).

## Local execution and data handling

This reference application is intended for a trusted local workstation and
controlled test calls. It is not a hosted service or a production softphone.

- Run the caller as a dedicated Calling test user with the documented OAuth scopes.
- Keep caller, answering-agent, and administrator sign-ins in separate browser profiles.
- Store credentials in the ignored `.env` file with owner-only permissions.
  The OAuth token file is stored with owner-only permissions. These files are
  plaintext; protect the workstation and revoke tokens when testing is complete.
- The browser run server binds to `127.0.0.1`, checks its exact Host and browser
  origin, rejects cross-site requests, and disables caching of token responses.
  This does not protect against another process running as your local user.
- Use synthetic speech and non-sensitive DTMF controls. Prepared audio and local
  artifacts can contain private test data; keep them out of Git and public issues.
  Artifacts hide the destination except its last four characters and redact the
  known runtime access token, but may retain call/device identifiers and
  third-party diagnostic text.
- Do not forward or expose the local run/OAuth listeners. Optional gateway
  monitoring access must remain restricted or use the documented private tunnel.

## Dependency security status

As of November 6, 2026, `npm audit` reports 84 findings in the installed dependency
tree: 3 critical, 8 high, 66 moderate, and 7 low. These are inherited dependencies;
the extraction does not establish which vulnerable paths are reachable in the
compiled browser client.

Vite was updated to 8.3.6 and Vitest to 4.1.12 during extraction. The Webex SDK
packages remain at their original locked versions to preserve calling behavior.
Remaining critical findings include `form-data`, `request`, and `shell-quote` in
the SDK's transitive tree. Resolving the SDK dependency tree requires a separate
compatibility review and live calling validation; a passing build is not that
validation. No clean dependency-audit claim is made for this sample.

Recheck from `web/` with `npm audit`. The application is a local, source-installed
test caller. Its HTTP servers bind to loopback, OAuth files are owner-readable
only, and credentials are excluded from Git. Keep deployment identifiers, tokens,
caller audio, and test artifacts out of commits.

The local Python 3.12 environment was also checked with `pip-audit` on November 6,
2026. It reported no known advisories across the installed third-party packages
after updating the bundled pip installer. The editable application itself was
excluded from that advisory lookup. This is a dated environment check, not a
guarantee for every version permitted by `pyproject.toml`.
