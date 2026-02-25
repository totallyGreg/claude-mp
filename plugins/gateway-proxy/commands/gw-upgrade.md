Guide a helm chart upgrade for kgateway and/or agentgateway.
$ARGUMENTS

If no arguments, check all components. If a component name is given (kgateway, agentgateway), upgrade only that.

Reference the gateway-proxy skill's `references/helm-lifecycle.md` for upgrade patterns and safety rules.

## Pre-upgrade Checks

1. Record current state for rollback:
```bash
helm list -n kgateway-system
helm history kgateway -n kgateway-system
helm history agentgateway -n kgateway-system
```

2. Backup current values:
```bash
helm get values kgateway -n kgateway-system -o yaml > /tmp/kgateway-values-backup.yaml
helm get values agentgateway -n kgateway-system -o yaml > /tmp/agentgateway-values-backup.yaml
```

3. Backup current resources:
```bash
kubectl get agentgatewaybackend,httproute,agentgatewaypolicy -n kgateway-system -o yaml > /tmp/gateway-resources-backup.yaml
```

4. Check latest versions:
```bash
gh api repos/kgateway-dev/kgateway/releases/latest --jq '.tag_name'
gh api repos/agentgateway/agentgateway/releases/latest --jq '.tag_name'
```

5. Check for breaking changes:
```bash
gh api repos/kgateway-dev/kgateway/releases/latest --jq '.body' | head -40
```

## Upgrade Commands

Present the upgrade commands in correct order. CRDs must be upgraded BEFORE controllers.

Upgrade order:
1. Gateway API CRDs (if needed)
2. kgateway-crds
3. kgateway controller
4. agentgateway-crds
5. agentgateway controller

Use safety flags: `--atomic --timeout 10m --wait --cleanup-on-fail`

## Post-upgrade Validation

After upgrade, verify:
```bash
kubectl get gateway,agentgatewaybackend,httproute -n kgateway-system
kubectl get pods -n kgateway-system -l 'app.kubernetes.io/name in (kgateway,agentgateway)'
kubectl -n kgateway-system logs -l app.kubernetes.io/name=kgateway --tail=20
kubectl -n kgateway-system logs -l app.kubernetes.io/name=agentgateway --tail=20
```

## Rollback (if needed)

```bash
helm rollback kgateway 0 -n kgateway-system --wait
helm rollback agentgateway 0 -n kgateway-system --wait
```

Present all commands for user approval before executing anything. Never auto-upgrade.
