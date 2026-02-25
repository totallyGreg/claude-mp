Compare installed kgateway and agentgateway helm chart versions against the latest GitHub releases.

Run the following commands to gather version information:

1. Installed versions:
```bash
helm list -n kgateway-system -o json 2>/dev/null | jq -r '.[] | "\(.name)\t\(.chart)\t\(.app_version)"' || echo "No helm releases found in kgateway-system"
```

2. Latest kgateway release:
```bash
gh api repos/kgateway-dev/kgateway/releases/latest --jq '{tag: .tag_name, date: .published_at, url: .html_url}' 2>/dev/null || echo "Could not fetch kgateway releases (is gh CLI installed and authenticated?)"
```

3. Latest agentgateway release:
```bash
gh api repos/agentgateway/agentgateway/releases/latest --jq '{tag: .tag_name, date: .published_at, url: .html_url}' 2>/dev/null || echo "Could not fetch agentgateway releases"
```

4. Gateway API CRD version:
```bash
kubectl get crd gateways.gateway.networking.k8s.io -o jsonpath='{.metadata.labels.gateway\.networking\.k8s\.io/bundle-version}' 2>/dev/null || echo "Gateway API CRDs not found"
```

Present results in a comparison table:

| Component | Installed | Latest | Status |
|-----------|-----------|--------|--------|
| kgateway-crds | ... | ... | Current / Update available |
| kgateway | ... | ... | Current / Update available |
| agentgateway-crds | ... | ... | Current / Update available |
| agentgateway | ... | ... | Current / Update available |
| Gateway API CRDs | ... | ... | Current / Update available |

Note: kgateway and agentgateway releases may use different version numbers as the projects diverge (kgateway v2.x, agentgateway v0.x). The K8s CRD charts for agentgateway still track kgateway versions for now.

If updates are available, show what's new by fetching release notes:
```bash
gh api repos/kgateway-dev/kgateway/releases/latest --jq '.body' | head -30
```

Suggest running `/gw-upgrade` if updates are available.

Reference the gateway-proxy skill's `references/helm-lifecycle.md` for version checking patterns.
