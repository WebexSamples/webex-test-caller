# Dependency security status

As of November 5, 2026, `npm audit` reports 84 findings in the installed dependency
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
