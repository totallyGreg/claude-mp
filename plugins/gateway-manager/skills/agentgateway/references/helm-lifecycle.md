# agentgateway Helm Lifecycle

Installation, upgrade, rollback, and version management for the agentgateway Helm chart.

## GitHub Repository

| Project | Repo | Releases | Registry |
|---------|------|----------|----------|
| agentgateway (AI data plane) | `agentgateway/agentgateway` | `gh api repos/agentgateway/agentgateway/releases` | `cr.agentgateway.dev/charts` |

**Note**: Starting v2.3.0, the agentgateway control plane migrates from the kgateway repo to `agentgateway/agentgateway`. The v2.2.x releases ship both from `kgateway-dev/kgateway`.

## Version Checking

```bash
# Installed agentgateway version
helm list -n kgateway-system -o json | jq '.[] | select(.name == "agentgateway") | {name: .name, version: .app_version, chart: .chart}'

# Latest agentgateway release
gh api repos/agentgateway/agentgateway/releases/latest --jq '.tag_name'

# Recent release notes
gh api repos/agentgateway/agentgateway/releases --jq '.[:3] | .[] | {tag: .tag_name, date: .published_at}'
```

## Installation Sequence

**Prerequisite**: kgateway must be installed first (see kgateway skill's `references/helm-lifecycle.md`).

```bash
# 4. agentgateway CRDs
helm upgrade -i agentgateway-crds oci://cr.agentgateway.dev/charts/agentgateway-crds \
  --version v2.2.1 --namespace kgateway-system

# 5. agentgateway controller
helm upgrade -i agentgateway oci://cr.agentgateway.dev/charts/agentgateway \
  --version v2.2.1 --namespace kgateway-system
```

## Upgrade Procedure

### Pre-Upgrade (Mandatory)

```bash
VERSION="v2.2.1"  # Target version

# 1. Record current state for rollback
helm history agentgateway -n kgateway-system

# 2. Backup current values
helm get values agentgateway -n kgateway-system -o yaml > /tmp/agentgateway-values-backup.yaml

# 3. Backup current resources
kubectl get agentgatewaybackend,agentgatewaypolicy -n kgateway-system -o yaml > /tmp/agentgateway-resources-backup.yaml

# 4. Check for breaking changes in release notes
gh api repos/agentgateway/agentgateway/releases/latest --jq '.body' | head -50
```

### Upgrade Execution

```bash
VERSION="v2.2.1"

# 1. agentgateway CRDs
helm upgrade agentgateway-crds oci://cr.agentgateway.dev/charts/agentgateway-crds \
  --version $VERSION --namespace kgateway-system --atomic --timeout 5m --wait

# 2. agentgateway controller
helm upgrade agentgateway oci://cr.agentgateway.dev/charts/agentgateway \
  --version $VERSION --namespace kgateway-system \
  --atomic --timeout 10m --wait --cleanup-on-fail
```

**Safety flags explained**:
- `--atomic`: Automatically rolls back on failure
- `--wait`: Waits for pods to be ready before declaring success
- `--cleanup-on-fail`: Deletes new resources created during a failed upgrade
- `--timeout`: Fail fast rather than hanging

### Post-Upgrade Validation

```bash
# 1. Check controller pods
kubectl get pods -n kgateway-system -l app.kubernetes.io/name=agentgateway

# 2. Verify rollout completed
kubectl rollout status deployment/ai-gateway -n kgateway-system --timeout=120s

# 3. Check logs for errors
kubectl -n kgateway-system logs -l app.kubernetes.io/name=agentgateway --tail=20

# 4. Verify resources are healthy
kubectl get agentgatewaybackend,agentgatewaypolicy -n kgateway-system

# 5. Verify routing works
gateway_address=$(kubectl get svc -n kgateway-system ai-gateway \
  -o jsonpath="{.status.loadBalancer.ingress[0]['hostname','ip']}")
curl -s "http://${gateway_address}:8080/ollama/v1/models" | head -5
```

## Rollback Procedure

```bash
# Tier 1: Automatic (if --atomic was used, already rolled back)

# Tier 2: Manual rollback to previous revision
helm rollback agentgateway 0 -n kgateway-system --wait

# Tier 3: Rollback to specific revision
helm history agentgateway -n kgateway-system  # Find target revision
helm rollback agentgateway <REVISION> -n kgateway-system --wait

# CRD rollback (manual — Helm does not rollback CRDs)
helm upgrade agentgateway-crds oci://cr.agentgateway.dev/charts/agentgateway-crds \
  --version <OLD_VERSION> --namespace kgateway-system
```

## Docs-vs-Reality Drift

Features documented on the `main` branch may not exist in released versions. Always inspect the installed CRD to verify field availability:

```bash
# Check what fields are available in the installed AgentgatewayBackend CRD
kubectl get crd agentgatewaybackends.agentgateway.dev -o json | \
  jq '.spec.versions[0].schema.openAPIV3Schema.properties.spec'

# Check available auth fields
kubectl get crd agentgatewaybackends.agentgateway.dev -o json | \
  jq '.spec.versions[0].schema.openAPIV3Schema.properties.spec.properties.policies.properties.auth'
```

## v2.3.0 Migration Notes

Starting with v2.3.0:
- agentgateway installs to **`agentgateway-system`** namespace (not `kgateway-system`)
- `enableAgentgateway` flag removed from kgateway helm chart
- agentgateway control plane moves to `agentgateway/agentgateway` repo
- agentgateway is now a **Linux Foundation** project (kgateway is CNCF sandbox)

```bash
# v2.3.0+ installation uses separate namespace
helm install agentgateway-crds oci://cr.agentgateway.dev/charts/agentgateway-crds \
  --namespace agentgateway-system --create-namespace
helm install agentgateway oci://cr.agentgateway.dev/charts/agentgateway \
  --namespace agentgateway-system
```

## Upgrade Safety Rules

1. **NEVER** upgrade CRDs and controllers in the same command
2. **ALWAYS** upgrade CRDs before controllers
3. **ALWAYS** backup values before upgrading: `helm get values <release> -o yaml > backup.yaml`
4. **ALWAYS** use `--atomic` for production upgrades (auto-rollback on failure)
5. **NEVER** use `--force` on gateway upgrades (it recreates resources, dropping connections)
6. **ALWAYS** verify health endpoints AND actual traffic routing after upgrade
7. Check for MAJOR version bumps — review CHANGELOG.md and release notes first
