# kgateway Helm Lifecycle

Installation, upgrade, rollback, and version management for the kgateway Helm chart.

## GitHub Repository

| Project | Repo | Releases | Registry |
|---------|------|----------|----------|
| kgateway (K8s control plane) | `kgateway-dev/kgateway` | `gh api repos/kgateway-dev/kgateway/releases` | `cr.kgateway.dev/kgateway-dev/charts` |
| Gateway API CRDs | `kubernetes-sigs/gateway-api` | `gh api repos/kubernetes-sigs/gateway-api/releases` | GitHub releases (kubectl apply) |

**Note**: Starting v2.3.0, the agentgateway control plane migrates from the kgateway repo to `agentgateway/agentgateway`. The v2.2.x releases ship both from `kgateway-dev/kgateway`.

## Version Checking

```bash
# Installed kgateway version
helm list -n kgateway-system -o json | jq '.[] | select(.name == "kgateway") | {name: .name, version: .app_version, chart: .chart}'

# Latest kgateway release
gh api repos/kgateway-dev/kgateway/releases/latest --jq '.tag_name'

# Gateway API CRD version
kubectl get crd gateways.gateway.networking.k8s.io \
  -o jsonpath='{.metadata.labels.gateway\.networking\.k8s\.io/bundle-version}'

# Recent release notes
gh api repos/kgateway-dev/kgateway/releases --jq '.[:3] | .[] | {tag: .tag_name, date: .published_at}'
```

## Installation Sequence

Install in this exact order — CRDs before controllers:

```bash
# 1. Gateway API CRDs (upstream)
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.1/standard-install.yaml

# 2. kgateway CRDs
helm upgrade -i kgateway-crds oci://cr.kgateway.dev/kgateway-dev/charts/kgateway-crds \
  --version v2.2.1 --namespace kgateway-system --create-namespace

# 3. kgateway controller (with agentgateway enabled)
helm upgrade -i kgateway oci://cr.kgateway.dev/kgateway-dev/charts/kgateway \
  --version v2.2.1 --namespace kgateway-system \
  --set controller.enableAgentgateway=true
```

**Note**: After installing kgateway, continue with agentgateway installation (see agentgateway skill's `references/helm-lifecycle.md`).

## Upgrade Procedure

### Pre-Upgrade (Mandatory)

```bash
VERSION="v2.2.1"  # Target version

# 1. Record current state for rollback
helm history kgateway -n kgateway-system

# 2. Backup current values
helm get values kgateway -n kgateway-system -o yaml > /tmp/kgateway-values-backup.yaml

# 3. Backup current resources
kubectl get gateway,httproute -n kgateway-system -o yaml > /tmp/gateway-resources-backup.yaml

# 4. Check for breaking changes in release notes
gh api repos/kgateway-dev/kgateway/releases/latest --jq '.body' | head -50

# 5. Preview changes with helm diff (if plugin installed)
helm diff upgrade kgateway oci://cr.kgateway.dev/kgateway-dev/charts/kgateway \
  --version $VERSION -n kgateway-system 2>/dev/null || echo "helm-diff plugin not installed"
```

### Upgrade Execution

```bash
VERSION="v2.2.1"

# 1. Gateway API CRDs (if needed)
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.1/standard-install.yaml

# 2. kgateway CRDs
helm upgrade kgateway-crds oci://cr.kgateway.dev/kgateway-dev/charts/kgateway-crds \
  --version $VERSION --namespace kgateway-system --atomic --timeout 5m --wait

# 3. kgateway controller
helm upgrade kgateway oci://cr.kgateway.dev/kgateway-dev/charts/kgateway \
  --version $VERSION --namespace kgateway-system \
  --set controller.enableAgentgateway=true \
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
kubectl get pods -n kgateway-system -l app.kubernetes.io/name=kgateway

# 2. Verify rollout completed
kubectl rollout status deployment/kgateway -n kgateway-system --timeout=120s

# 3. Check logs for errors
kubectl -n kgateway-system logs -l app.kubernetes.io/name=kgateway --tail=20

# 4. Verify gateway resources
kubectl get gateway,httproute -n kgateway-system
```

## Rollback Procedure

```bash
# Tier 1: Automatic (if --atomic was used, already rolled back)

# Tier 2: Manual rollback to previous revision
helm rollback kgateway 0 -n kgateway-system --wait

# Tier 3: Rollback to specific revision
helm history kgateway -n kgateway-system  # Find target revision
helm rollback kgateway <REVISION> -n kgateway-system --wait

# CRD rollback (manual — Helm does not rollback CRDs)
helm upgrade kgateway-crds oci://cr.kgateway.dev/kgateway-dev/charts/kgateway-crds \
  --version <OLD_VERSION> --namespace kgateway-system
```

**Rollback caveats**:
- CRDs are NOT rolled back by `helm rollback` — must be done manually
- If CRD schema changed and existing CRs were migrated, rollback may leave CRs incompatible
- `helm rollback` creates a NEW revision (does not revert history)

## Docs-vs-Reality Drift

Features documented on the `main` branch may not exist in released versions. Always inspect the installed CRD to verify field availability:

```bash
# Check what fields are available in the installed CRD
kubectl get crd backends.gateway.kgateway.dev -o json | \
  jq '.spec.versions[0].schema.openAPIV3Schema.properties.spec' 2>/dev/null
```

## v2.3.0 Migration Notes

Starting with v2.3.0:
- `enableAgentgateway` flag removed from kgateway helm chart
- agentgateway installs to **`agentgateway-system`** namespace (not `kgateway-system`)
- agentgateway control plane moves to `agentgateway/agentgateway` repo
- kgateway focuses on Envoy-based Gateway API only

## Upgrade Safety Rules

1. **NEVER** upgrade CRDs and controllers in the same command
2. **ALWAYS** upgrade CRDs before controllers
3. **ALWAYS** backup values before upgrading: `helm get values <release> -o yaml > backup.yaml`
4. **ALWAYS** use `--atomic` for production upgrades (auto-rollback on failure)
5. **NEVER** use `--force` on gateway upgrades (it recreates resources, dropping connections)
6. **ALWAYS** verify health endpoints AND actual traffic routing after upgrade
7. **NEVER** skip `helm diff` before upgrading (if available)
8. Check for MAJOR version bumps — review CHANGELOG.md and release notes first
