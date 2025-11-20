# Helm 4 Evolution Reference

Comprehensive guide to Helm 4 features, changes, and migration from Helm 3.

## Timeline and Versions

- **Helm 3.0**: Released November 2019
- **Helm 3.8**: January 2022 - OCI support becomes stable
- **Helm 3.12**: May 2023 - Latest 3.x stable as of October 2025
- **Helm 4.0 Beta**: October 2025 (v4.0.0-beta.2)
- **Helm 4.0 GA**: Expected November 2025
- **Helm 3 Support**: Will continue for 12 months after Helm 4 GA

## What's New in Helm 4

### 1. Enhanced OCI Support

#### Improved Performance
- Faster chart push/pull operations
- Better caching mechanisms
- Optimized dependency resolution
- Reduced network overhead

#### Native OCI Features
```bash
# Direct registry operations
helm registry list
helm registry info oci://registry.example.com/charts/mychart

# Improved authentication handling
helm registry login registry.example.com --insecure-skip-tls-verify

# Better error messages
helm push mychart-1.0.0.tgz oci://registry.example.com/charts
# Error: authentication required (401)
# Hint: Run 'helm registry login registry.example.com' first
```

#### OCI Annotations
```yaml
# Chart.yaml supports OCI-specific annotations
annotations:
  org.opencontainers.image.created: "2025-10-31T12:00:00Z"
  org.opencontainers.image.authors: "John Doe <john@example.com>"
  org.opencontainers.image.url: "https://example.com/mychart"
  org.opencontainers.image.documentation: "https://docs.example.com/mychart"
  org.opencontainers.image.source: "https://github.com/example/mychart"
  org.opencontainers.image.version: "1.0.0"
  org.opencontainers.image.revision: "abc123"
  org.opencontainers.image.vendor: "Example Corp"
  org.opencontainers.image.licenses: "Apache-2.0"
  org.opencontainers.image.title: "My Chart"
  org.opencontainers.image.description: "A Helm chart for Kubernetes"
```

### 2. Dependency Management Improvements

#### Better Dependency Resolution
```bash
# Faster dependency updates
helm dependency update mychart/  # Much faster in Helm 4

# Better conflict resolution
# Helm 4 provides clearer error messages when dependencies conflict

# Dependency tree visualization
helm dependency tree mychart/
```

#### Lock File Enhancements
```yaml
# Chart.lock now includes more metadata
dependencies:
- name: postgresql
  repository: oci://registry-1.docker.io/bitnamicharts
  version: 12.1.0
  digest: sha256:abc123...  # Added in Helm 4
  resolved: oci://registry-1.docker.io/bitnamicharts/postgresql:12.1.0
```

### 3. Template Engine Improvements

#### New Functions
```yaml
# randPassword - Generate cryptographically secure passwords
password: {{ randPassword 32 | b64enc }}

# toRawJson - Output JSON without escaping
config: {{ .Values.config | toRawJson }}

# sha512sum - Additional hash function
checksum: {{ .Values.data | sha512sum }}

# semver - Semantic version comparisons
{{- if semverCompare ">=1.24.0" .Capabilities.KubeVersion.Version }}
# Use v1 Ingress
{{- end }}

# compact - Remove nil/empty values from lists
items: {{ list "a" "" "b" nil "c" | compact }}

# mustRegexMatch - Required regex match
{{- mustRegexMatch "^[a-z]+$" .Values.name }}
```

#### Improved Error Messages
```yaml
# Helm 3
Error: template: mychart/templates/deployment.yaml:10:14: executing "mychart/templates/deployment.yaml" at <.Values.undefined>: nil pointer evaluating interface {}.undefined

# Helm 4
Error: template: mychart/templates/deployment.yaml:10:14: undefined value
  at: .Values.undefined
  template: mychart/templates/deployment.yaml
  line: 10
  Hint: Check if 'undefined' is defined in values.yaml
```

### 4. CLI Enhancements

#### Improved Commands
```bash
# helm diff is now built-in (no plugin needed)
helm diff upgrade my-release ./mychart

# Better search
helm search oci registry.example.com/charts --versions

# Chart inspection improvements
helm show all oci://registry.example.com/charts/mychart --version 1.0.0

# Enhanced output formats
helm list -o json | jq '.[] | select(.status == "deployed")'
helm history my-release -o yaml
```

#### New Flags
```bash
# --cascade option for upgrades
helm upgrade my-release ./mychart --cascade=foreground

# --create-namespace is now the default behavior
helm install my-release ./mychart --namespace prod

# --timeout improvements
helm install my-release ./mychart --timeout 10m --wait

# Better dry-run
helm install my-release ./mychart --dry-run=server --validate
```

### 5. Performance Improvements

#### Faster Operations
- Chart rendering: ~30% faster
- Dependency resolution: ~50% faster
- OCI operations: ~40% faster
- Template compilation: ~25% faster

#### Memory Usage
- Reduced memory footprint for large charts
- Better streaming for large values files
- Optimized template caching

### 6. Kubernetes API Updates

#### Support for Latest K8s Versions
```yaml
# Helm 4 supports Kubernetes 1.24-1.30
kubeVersion: ">=1.24.0-0 <1.31.0-0"

# Better API version handling
{{- if .Capabilities.APIVersions.Has "networking.k8s.io/v1/Ingress" }}
# Use v1 Ingress
{{- else if .Capabilities.APIVersions.Has "networking.k8s.io/v1beta1/Ingress" }}
# Use v1beta1 Ingress
{{- end }}
```

#### Deprecated API Warnings
```bash
# Helm 4 warns about deprecated APIs
helm install my-release ./mychart
Warning: Chart uses deprecated API version extensions/v1beta1 for Deployment
Recommendation: Update to apps/v1
```

### 7. Security Enhancements

#### Built-in Verification
```bash
# Cosign verification built-in
helm install my-release oci://registry.example.com/charts/mychart \
  --verify-cosign \
  --cosign-key cosign.pub

# SBOM support
helm show sbom oci://registry.example.com/charts/mychart
```

#### Provenance Improvements
```bash
# Enhanced provenance files
helm package --sign --key 'My Key' --keyring ~/.gnupg/secring.gpg mychart/
# Includes more metadata: build info, commit hash, build timestamp
```

## Breaking Changes

### 1. Command Changes

#### Removed Commands
```bash
# REMOVED in Helm 4
helm repo index     # Use OCI registries instead

# CHANGED
helm install --name my-release ./mychart  # --name flag removed
helm install my-release ./mychart         # Correct syntax
```

#### Changed Behavior
```bash
# Helm 3: Creates namespace if doesn't exist with --create-namespace
helm install my-release ./mychart --namespace prod --create-namespace

# Helm 4: Creates namespace by default
helm install my-release ./mychart --namespace prod
# Add --no-create-namespace to prevent creation
```

### 2. Repository Changes

#### Classic Repositories Deprecated
```bash
# Helm 3: Classic HTTP repositories
helm repo add myrepo https://charts.example.com

# Helm 4: Still supported but deprecated
# Warning: Classic chart repositories are deprecated. Consider migrating to OCI.

# Helm 4: Preferred OCI approach
helm registry login registry.example.com
helm install my-release oci://registry.example.com/charts/mychart
```

#### Chart.yaml Changes
```yaml
# Helm 3
dependencies:
  - name: postgresql
    version: "12.1.0"
    repository: "https://charts.bitnami.com/bitnami"

# Helm 4: Still works but warning issued
# Warning: Classic repository URLs are deprecated

# Helm 4: Preferred
dependencies:
  - name: postgresql
    version: "12.1.0"
    repository: "oci://registry-1.docker.io/bitnamicharts"
```

### 3. API Version Requirements

```yaml
# Helm 3: apiVersion: v2 required
apiVersion: v2
name: mychart
version: 1.0.0

# Helm 4: apiVersion: v2 still required
# No change, but validation is stricter
apiVersion: v2
name: mychart
version: 1.0.0
type: application  # Now enforced (application or library)
```

### 4. Go Template Changes

#### Stricter Validation
```yaml
# Helm 3: Silently ignores undefined values
value: {{ .Values.undefined.key }}  # Returns empty string

# Helm 4: Errors by default (can be configured)
value: {{ .Values.undefined.key }}
# Error: undefined value at .Values.undefined

# Use default to prevent errors
value: {{ .Values.undefined.key | default "" }}
```

### 5. Hook Changes

```yaml
# Helm 3: Hook weights as strings accepted
annotations:
  "helm.sh/hook-weight": "5"

# Helm 4: Must be integers
annotations:
  "helm.sh/hook-weight": "5"  # Warning: use integer
  "helm.sh/hook-weight": 5    # Correct
```

## Migration Guide

### Step 1: Assess Current Charts

```bash
# Check Helm version
helm version

# Lint charts with Helm 4 beta
helm lint ./mychart --strict

# Render templates to check for issues
helm template test ./mychart --validate

# Check for deprecated features
helm template test ./mychart 2>&1 | grep -i "warning\|deprecated"
```

### Step 2: Update Chart.yaml

```yaml
# Before (Helm 3)
apiVersion: v2
name: mychart
version: 1.0.0
dependencies:
  - name: redis
    version: "17.0.0"
    repository: "https://charts.bitnami.com/bitnami"

# After (Helm 4 ready)
apiVersion: v2
name: mychart
version: 2.0.0  # Bump major version for breaking changes
type: application
dependencies:
  - name: redis
    version: "17.0.0"
    repository: "oci://registry-1.docker.io/bitnamicharts"
annotations:
  org.opencontainers.image.source: "https://github.com/example/mychart"
```

### Step 3: Update Templates

#### Fix Undefined Value Access
```yaml
# Before
env:
- name: OPTIONAL_VAR
  value: {{ .Values.optional.value }}

# After - Use default
env:
- name: OPTIONAL_VAR
  value: {{ .Values.optional.value | default "" }}

# Or check existence
{{- if .Values.optional }}
- name: OPTIONAL_VAR
  value: {{ .Values.optional.value }}
{{- end }}
```

#### Update Deprecated APIs
```yaml
# Before (Helm 3)
apiVersion: extensions/v1beta1
kind: Ingress

# After (Helm 4)
apiVersion: networking.k8s.io/v1
kind: Ingress
spec:
  ingressClassName: nginx  # Required in v1
```

#### Fix Hook Annotations
```yaml
# Before
annotations:
  "helm.sh/hook-weight": "5"
  "helm.sh/hook-delete-policy": "before-hook-creation,hook-succeeded"

# After
annotations:
  "helm.sh/hook-weight": 5  # Integer, not string
  "helm.sh/hook-delete-policy": "before-hook-creation,hook-succeeded"
```

### Step 4: Update Dependencies

```bash
# Update Chart.yaml dependencies to OCI
# Then update lock file
helm dependency update ./mychart

# Verify
helm dependency list ./mychart
```

### Step 5: Test with Helm 4 Beta

```bash
# Install Helm 4 beta alongside Helm 3
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-4 | bash

# Test rendering
helm4 template test ./mychart --validate

# Test installation in test cluster
helm4 install test ./mychart --dry-run --debug

# Test upgrade
helm4 upgrade test ./mychart --dry-run --debug
```

### Step 6: Update CI/CD

#### GitHub Actions
```yaml
# Before
- name: Set up Helm
  uses: azure/setup-helm@v3
  with:
    version: v3.12.0

# After
- name: Set up Helm
  uses: azure/setup-helm@v3
  with:
    version: v4.0.0

# Add OCI login
- name: Login to OCI registry
  run: |
    echo ${{ secrets.REGISTRY_PASSWORD }} | \
      helm registry login registry.example.com \
      --username ${{ secrets.REGISTRY_USERNAME }} \
      --password-stdin
```

#### Migration Script
```bash
#!/bin/bash
# migrate-to-helm4.sh

set -e

CHART_DIR="${1:-.}"

echo "==> Checking Helm 4 compatibility..."

# Check for classic repo URLs
if grep -r "repository:.*https://" "$CHART_DIR/Chart.yaml"; then
  echo "WARNING: Found classic repository URLs"
  echo "Consider migrating to OCI registries"
fi

# Check for string hook weights
if grep -r 'helm.sh/hook-weight.*:.*"' "$CHART_DIR/templates"; then
  echo "WARNING: Found string hook weights"
  echo "Convert to integers in Helm 4"
fi

# Check for deprecated APIs
helm template test "$CHART_DIR" 2>&1 | grep -i "deprecated" || true

# Test with Helm 4
echo "==> Testing with Helm 4..."
helm template test "$CHART_DIR" --validate

echo "==> Migration check complete!"
```

### Step 7: Release Strategy

#### Semantic Versioning
```yaml
# If breaking changes for users
version: 2.0.0

# If only internal Helm 4 compatibility
version: 1.5.0

# Document in CHANGELOG.md
## [2.0.0] - 2025-11-15
### Breaking Changes
- Migrated to OCI dependencies (Helm 4 recommended)
- Requires Helm 3.8+ or Helm 4+

### Changed
- Updated all dependencies to OCI format
- Fixed hook weight types for Helm 4 compatibility
```

## Compatibility Matrix

| Feature | Helm 3.8+ | Helm 4 | Notes |
|---------|-----------|--------|-------|
| OCI Charts | ✅ Stable | ✅ Enhanced | Helm 4 has better performance |
| Classic Repos | ✅ Supported | ⚠️ Deprecated | Will be removed in Helm 5 |
| Chart API v2 | ✅ Required | ✅ Required | No change |
| GPG Signing | ✅ Supported | ✅ Supported | Enhanced in Helm 4 |
| Cosign | 🔌 Plugin | ✅ Built-in | Native support in Helm 4 |
| K8s 1.24-1.27 | ✅ Supported | ✅ Supported | Full support |
| K8s 1.28-1.30 | ⚠️ Limited | ✅ Full | Better support in Helm 4 |

## Testing Checklist

### Pre-Migration
- [ ] All charts pass `helm lint --strict`
- [ ] All charts have passing unit tests
- [ ] Dependencies are pinned to specific versions
- [ ] No deprecated Kubernetes APIs
- [ ] Documentation is up to date

### During Migration
- [ ] Chart.yaml updated to OCI dependencies
- [ ] Hook weights converted to integers
- [ ] Undefined value accesses use defaults
- [ ] Templates validated with Helm 4
- [ ] Integration tests pass with Helm 4

### Post-Migration
- [ ] Charts work with both Helm 3.8+ and Helm 4
- [ ] CI/CD updated for Helm 4
- [ ] Documentation updated with Helm 4 requirements
- [ ] Changelog includes migration notes
- [ ] Users notified of changes

## FAQ

### Q: Do I need to upgrade immediately?
**A:** No. Helm 3 will be supported for 12 months after Helm 4 GA. However, starting migration early is recommended.

### Q: Will my Helm 3 charts work with Helm 4?
**A:** Most charts will work without changes. Charts using classic repositories will get deprecation warnings.

### Q: Should I migrate to OCI?
**A:** Yes. OCI is the future of Helm charts. Classic repositories will be removed in Helm 5.

### Q: Can I use Helm 3 and Helm 4 together?
**A:** Yes. They can coexist. Releases are compatible between versions.

### Q: What about Helm 2?
**A:** Helm 2 reached end-of-life in November 2020. Migrate to Helm 3 or 4.

### Q: Will Helm 4 break my existing releases?
**A:** No. Helm 4 can manage releases created by Helm 3.

### Q: How do I test Helm 4 compatibility?
**A:** Install Helm 4 beta and run `helm template` and `helm lint` on your charts.

### Q: When should I bump my chart version?
**A:** Bump major version if you make breaking changes for users. Minor version for Helm 4 compatibility changes.

## Resources

### Official Documentation
- Helm 4 Release Notes: https://github.com/helm/helm/releases/tag/v4.0.0
- Migration Guide: https://helm.sh/docs/topics/v4_migration/
- OCI Guide: https://helm.sh/docs/topics/registries/

### Community
- Helm Slack: #helm-users on Kubernetes Slack
- GitHub Discussions: https://github.com/helm/helm/discussions
- Stack Overflow: Tag `helm` and `helm4`

### Tools
- Helm Diff: Built-in to Helm 4
- helm-unittest: https://github.com/helm-unittest/helm-unittest
- chart-testing: https://github.com/helm/chart-testing
- kubeconform: https://github.com/yannh/kubeconform

---

**Last Updated**: October 31, 2025
**Helm 4 Status**: Beta (v4.0.0-beta.2)
**Helm 4 GA Expected**: November 2025
