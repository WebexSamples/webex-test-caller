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

As of November 6, 2026, a clean `npm ci` followed by `npm audit` reports
55 findings: **0 critical, 0 high, 49 moderate, and 6 low**, down from 84 findings
(including 3 critical and 8 high). npm includes dependent-package findings in
these totals; the remaining findings originate in three packages below. This
is not a clean dependency-audit claim or a complete reachability assessment.

The Calling and Webex SDK packages are synchronized at 3.13.0. The lockfile
refreshes compatible transitive updates, and `web/package.json` contains
these temporary overrides until upstream dependencies catch up:

- Replace abandoned `request` with the maintained
  [`@cypress/request` fork](https://github.com/cypress-io/request) at 4.0.1.
  This also replaces its vulnerable cookie and multipart dependencies.
- Use patched `ws` 8.22.1 and AJV 6.15.0 within their existing major versions.
- Use UUID 11.1.1 for dependencies already using the named-export API (versions
  7 through 10). Legacy SDK consumers require the old callable default export
  and remain on their original versions.
- Use patched Glob 14.0.4 and Minimatch 11.0.5 for Expo fingerprinting, a
  transitive dependency of the full SDK. The browser caller does not run Expo
  fingerprinting; compatibility tests exercise its glob and ignore-pattern APIs.

Compatibility tests cover the HTTP callback/multipart API, both UUID export
shapes, and fingerprint glob/ignore behavior. SDK updates also require a live
Calling check; a passing build alone does not validate registration or media.
Remove overrides when the SDK's dependency declarations adopt patched versions.

Remaining upstream work:

| Package | Advisory | Upgrade constraint |
| --- | --- | --- |
| `elliptic` | [GHSA-848j-6mx2-7j84](https://github.com/advisories/GHSA-848j-6mx2-7j84), low | No published patched version; inherited through browser crypto polyfills. Replacing cryptographic implementations requires a separate reviewed change. |
| `file-type` | [GHSA-5v7r-6r5c-r473](https://github.com/advisories/GHSA-5v7r-6r5c-r473), moderate | The patch is in 21.3.1; the SDK HTTP client uses the older CommonJS `fromBuffer` API. A major-version override would break that API. |
| legacy `uuid` | [GHSA-w5hq-g745-h8pq](https://github.com/advisories/GHSA-w5hq-g745-h8pq), moderate | SDK/core and KMS consumers use a callable default export removed from patched UUID versions. The advisory concerns v3/v5/v6 output-buffer bounds; preserving v4 callers does not remove the installed advisory. |

Recheck from `web/` with `npm audit`. CI runs `npm audit --audit-level=high`
and fails for any high or critical finding; moderate and low findings remain
visible in its output. No audit packages or advisories are excluded.

The application is a local, source-installed test caller. Its HTTP servers bind
to loopback, OAuth files are owner-readable only, and credentials are excluded
from Git. Keep deployment identifiers, tokens, caller audio, and test artifacts
out of commits.

The local Python 3.12 environment was also checked with `pip-audit` on November 6,
2026. It reported no known advisories across the installed third-party packages
after updating the bundled pip installer. The editable application itself was
excluded from that advisory lookup. This is a dated environment check, not a
guarantee for every version permitted by `pyproject.toml`.
