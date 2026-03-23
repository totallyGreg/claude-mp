# kgateway

kgateway is a CNCF sandbox project implementing the Kubernetes Gateway API with an Envoy-based data plane. Use this skill when working with Gateway, HTTPRoute, or GatewayClass resources in a kgateway-managed cluster, or when installing and upgrading kgateway via Helm. It is distinct from agentgateway: starting v2.3.0 these are separate projects — kgateway focuses on Envoy-based Gateway API routing, while agentgateway handles AI/MCP backends in its own namespace.

## Capabilities

- Create and configure Gateway resources with listener definitions and LoadBalancer services
- Define HTTPRoutes with path-based matching, URL rewriting, and parentRef attachment
- Disambiguate GatewayClass selection between `kgateway` (Backend CRD) and `agentgateway` (AgentgatewayBackend CRD)
- Install and upgrade kgateway and its CRDs via Helm with pre/post validation
- Troubleshoot common errors including immutable selector conflicts, route attachment failures, and 404s from missing path rewrites
- Run diagnostic slash commands (`/gw-status`, `/gw-debug`, `/gw-logs`, `/gw-route`, `/gw-versions`, `/gw-upgrade`) for gateway operations

## Current Metrics

*Last evaluated: 2026-03-22*

| Metric | Score | Interpretation |
|--------|-------|----------------|
| Conciseness | 98/100 | Excellent |
| Complexity | 90/100 | Good |
| Spec Compliance | 80/100 | Good |
| Progressive Disclosure | 100/100 | Excellent |
| Description Quality | 100/100 | Excellent |
| **Overall** | **91/100** | **Good** |

Run `uv run scripts/evaluate_skill.py <path> --explain` for improvement suggestions.

## Version History

| Version | Date | Issue | Summary | Conc | Comp | Spec | Disc | Desc | Overall |
|---------|------|-------|---------|------|------|------|------|------|---------|
| 1.0.0 | 2026-02-25 | [#61](https://github.com/totallyGreg/claude-mp/issues/61) | Split from gateway-proxy v2.0.0; kgateway-focused skill | 98 | 90 | 80 | 100 | - | 91 |

**Metric Legend:** Conc=Conciseness, Comp=Complexity, Spec=Spec Compliance, Disc=Progressive Disclosure, Desc=Description Quality (0-100 scale)

## Active Work

- None.

## Known Issues

- None.

## Archive

- Git history: `git log --grep="kgateway"`
- Closed issues: https://github.com/totallyGreg/claude-mp/issues?q=label:enhancement+is:closed

---

*Run `uv run scripts/evaluate_skill.py <path> --update-readme` to refresh metrics.*
