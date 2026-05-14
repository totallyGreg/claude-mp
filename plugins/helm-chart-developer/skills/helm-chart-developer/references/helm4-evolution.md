---
last_verified: 2026-04-29
sources:
  - type: github
    repo: "helm/helm"
    paths: ["cmd/", "pkg/"]
    description: "Helm CLI source — releases, new features, breaking changes"
  - type: web
    url: "https://helm.sh/blog/"
    description: "Helm blog — release announcements and migration guides"
---

# Helm Evolution Reference

Guide to recent Helm 3.x features and Helm 4, including migration from Helm 3 to Helm 4.

## Release Timeline

| Version | Date | Highlights |
|---------|------|------------|
| 3.15.0 | 2024-05-15 | `--hide-secret` for dry-run |
| 3.16.0 | 2024-09-11 | `sha512sum` function, `--skip-schema-validation` flag |
| 3.17.0 | 2025-01-15 | OCI digest pull, `--take-ownership`, `toYamlPretty` |
| 3.18.0 | 2025-05-19 | JSON Schema 2020-12, ORAS v2, mTLS proxy |
| 3.19.0 | 2025-09-11 | Stabilization, `helm create` adds HTTPRoute |
| 3.20.x | 2026-01-21 | Maintenance mode, k8s API v0.35.0 |
| **4.0.0 GA** | **2025-11-12** | **Production-ready release** |
| 4.1.1 | 2026-01-21 | `--wait=hookOnly`, concurrent dep builds |
| 4.1.3 | 2026-03-11 | Fix `--dry-run=server` not respecting `generateName` |
| 3.20.1 | 2026-03-12 | Patch release |
| **4.1.4** | **2026-04-09** | **Security: 3 CVEs — chart extraction path traversal, plugin `.prov` verification bypass, plugin metadata path traversal** |
| 3.20.2 | 2026-04-09 | Security patch (same CVEs backported) |

Helm 3.x and 4.x are maintained in parallel. Next releases: 4.2.0 / 3.21.0 on May 13, 2026.

### Security Advisory: v4.1.4 / v3.20.2 (2026-04-09)

Three CVEs fixed — upgrade immediately:

| CVE | Severity | Description |
|-----|----------|-------------|
| GHSA-hr2v-4r36-88hr | High | Chart extraction path traversal via `Chart.yaml` name dot-segment |
| GHSA-q5jf-9vfq-h4h7 | Medium | Plugin verification fails open when `.prov` file is missing |
| GHSA-vmx8-mqv2-9gmg | High | Plugin metadata version enables arbitrary file write outside plugin directory |

## Recent Helm 3.x Features (3.15–3.20)

### 3.15: Secret Hiding
```bash
# Hide secrets during dry-run
helm install --dry-run --hide-secret myrelease mychart/
```

### 3.16: Schema Control & sha512sum
```bash
# Skip schema validation (useful for debugging)
helm install myrelease mychart/ --skip-schema-validation
helm lint mychart/ --skip-schema-validation
```
```yaml
# sha512sum template function
checksum: {{ .Values.data | sha512sum }}
```

### 3.17: OCI Digest & Resource Adoption
```bash
# Pull/install by OCI digest (immutable reference)
helm pull oci://registry.example.com/charts/mychart@sha256:abc123...
helm install myrelease oci://registry.example.com/charts/mychart@sha256:abc123...

# Adopt existing cluster resources into a Helm release
helm install myrelease mychart/ --take-ownership
helm upgrade myrelease mychart/ --take-ownership
```
```yaml
# toYamlPretty template function — formatted YAML output
config: {{ .Values.config | toYamlPretty | nindent 2 }}
```
```bash
# Auth flags on push and dependency commands
helm push mychart-1.0.0.tgz oci://registry.example.com/charts --username user --password pass
helm dependency update mychart/ --username user --password pass
```

### 3.18: JSON Schema 2020 & ORAS v2
- `values.schema.json` now supports JSON Schema 2020-12 draft (`$schema: "https://json-schema.org/draft/2020-12/schema"`)
- Internal OCI library upgraded from ORAS v1 to v2
- Automatic HTTP fallback for OCI registries
- CPU and memory profiling support

### 3.19: Gateway API & Stabilization
- `helm create` scaffolded templates now include **HTTPRoute** from Gateway API
- Fixed ORAS v2 regressions (OCI pull with `--password`, JSON Schema `$ref` URLs)
- Fixed charts failing with redirect registries

### 3.20: Maintenance Mode
- Backports from Helm 4, bumped k8s API versions to v0.35.0
- Fixed `helm uninstall --keep-history` not suspending previous deployed releases

## Helm 4 — What's Actually New

Helm 4.0.0 GA released November 12, 2025. Changes are less extensive than Helm 2→3.

### Key New Features

1. **WebAssembly (Wasm) Plugin System**: Plugins can now be written as Wasm modules in addition to traditional executables
2. **Post-renderers are plugins**: The post-renderer interface is now part of the plugin system
3. **Server-side apply**: Replaces client-side 3-way merge for more reliable resource updates
4. **kstatus resource watching**: Improved wait/readiness detection using kstatus-based monitoring
5. **Local content-based caching**: Charts cached by content hash for faster operations
6. **Structured logging via slog**: SDK logging uses Go's structured logger
7. **Reproducible chart builds**: `helm package` produces deterministic archives
8. **Multiple chart API versions**: Experimental support for v3 chart API alongside v2

### Backward Compatibility
- **Charts with `apiVersion: v2` continue to work** in Helm 4 without changes
- Existing charts should install/upgrade without modification
- Helm 4 can manage releases created by Helm 3

### Helm 4.1 Additions
```bash
# Wait strategy selection
helm install myrelease mychart/ --wait=hookOnly

# Scripting-friendly output
helm repo list --no-headers
```
- Concurrent dependency builds with atomic file writes
- Improved logging: chart name in dependency logs, namespace in resource waiting logs
- Confirmation message when all resources are ready

## Breaking Changes in Helm 4

### Classic Repositories Deprecated
```bash
# Still works but issues deprecation warning
helm repo add myrepo https://charts.example.com
# Warning: Classic chart repositories are deprecated. Consider migrating to OCI.

# Preferred: OCI registries
helm install myrelease oci://registry.example.com/charts/mychart
```

### Chart.yaml Dependencies
```yaml
# Deprecated (warning issued)
dependencies:
  - name: postgresql
    version: "12.1.0"
    repository: "https://charts.bitnami.com/bitnami"

# Preferred
dependencies:
  - name: postgresql
    version: "12.1.0"
    repository: "oci://registry-1.docker.io/bitnamicharts"
```

### Stricter Validation
```yaml
# Chart.yaml type field now enforced
apiVersion: v2
name: mychart
version: 1.0.0
type: application  # Must be "application" or "library"
```

## Migration Guide (Helm 3 → Helm 4)

### Step 1: Verify Compatibility
```bash
helm version  # Check current version
helm lint mychart/ --strict
helm template test mychart/ --validate
```

### Step 2: Update Dependencies to OCI
```yaml
# Chart.yaml — switch to OCI repository URLs
dependencies:
  - name: redis
    version: "17.0.0"
    repository: "oci://registry-1.docker.io/bitnamicharts"
```
```bash
helm dependency update mychart/
```

### Step 3: Test with Helm 4
```bash
# Install Helm 4 and test
helm template test mychart/ --validate
helm install test mychart/ --dry-run --debug
```

### Step 4: Update CI/CD
```yaml
# GitHub Actions example
- name: Set up Helm
  uses: azure/setup-helm@v3
  with:
    version: v4.1.3  # Latest stable

- name: Login to OCI registry
  run: |
    echo ${{ secrets.REGISTRY_PASSWORD }} | \
      helm registry login registry.example.com \
      --username ${{ secrets.REGISTRY_USERNAME }} \
      --password-stdin
```

## Compatibility Matrix

| Feature | Helm 3.17+ | Helm 4.x | Notes |
|---------|-----------|--------|-------|
| OCI Charts | Stable | Enhanced | Digest refs in 3.17+, caching in 4.x |
| Classic Repos | Supported | Deprecated | Will be removed in future |
| Chart API v2 | Required | Required | No change needed |
| JSON Schema 2020 | 3.18+ | Yes | 2020-12 draft support |
| Server-side Apply | No | Yes | Replaces 3-way merge |
| Wasm Plugins | No | Yes | New plugin architecture |
| GPG Signing | Supported | Supported | No change |
| Gateway API (HTTPRoute) | 3.19+ scaffold | Yes | `helm create` includes it |

## Migration Checklist

### Pre-Migration
- [ ] All charts pass `helm lint --strict`
- [ ] All charts have passing unit tests
- [ ] Dependencies are pinned to specific versions
- [ ] No deprecated Kubernetes APIs in templates
- [ ] Documentation is up to date

### During Migration
- [ ] Chart.yaml dependencies updated to OCI URLs
- [ ] Chart.yaml includes `type: application` or `type: library`
- [ ] Templates validated with Helm 4
- [ ] Unit tests pass with Helm 4
- [ ] CI/CD updated for Helm 4

### Post-Migration
- [ ] Charts work with both Helm 3.17+ and Helm 4
- [ ] Changelog includes migration notes
- [ ] Users notified of changes

---

**Last Updated**: March 30, 2026
**Latest Helm 3.x**: 3.20.1 (March 12, 2026)
**Latest Helm 4.x**: 4.1.3 (March 11, 2026)
