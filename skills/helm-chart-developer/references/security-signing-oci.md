# Security, Signing, and OCI Registry Reference

Complete guide to securing Helm charts, GPG signing, and working with OCI registries.

## Part 1: Chart Security Best Practices

> **💡 Quick Start**: For complete External Secrets integration examples with Vault, AWS, Azure, and GCP,
> see `real-world-patterns.md` Pattern 8.



### 1. Security Contexts

#### Pod Security Context

```yaml
# templates/deployment.yaml
spec:
  template:
    spec:
      # Pod-level security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 3000
        fsGroup: 2000
        fsGroupChangePolicy: "OnRootMismatch"
        seccompProfile:
          type: RuntimeDefault
        supplementalGroups:
          - 4000
```

#### Container Security Context

```yaml
containers:
- name: {{ .Chart.Name }}
  securityContext:
    allowPrivilegeEscalation: false
    readOnlyRootFilesystem: true
    runAsNonRoot: true
    runAsUser: 1000
    capabilities:
      drop:
      - ALL
      add:
      - NET_BIND_SERVICE  # Only if needed
    seccompProfile:
      type: RuntimeDefault
```

#### Values Template

```yaml
# values.yaml
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 2000
  seccompProfile:
    type: RuntimeDefault

securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1000
  capabilities:
    drop:
    - ALL
```

### 2. RBAC Configuration

#### ServiceAccount

```yaml
# templates/serviceaccount.yaml
{{- if .Values.serviceAccount.create -}}
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "mychart.serviceAccountName" . }}
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
  {{- with .Values.serviceAccount.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
automountServiceAccountToken: {{ .Values.serviceAccount.automount }}
{{- end }}
```

#### Role

```yaml
# templates/role.yaml
{{- if .Values.rbac.create -}}
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {{ include "mychart.fullname" . }}
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]
  resourceNames: ["specific-secret-name"]  # Limit scope!
{{- end }}
```

#### RoleBinding

```yaml
# templates/rolebinding.yaml
{{- if .Values.rbac.create -}}
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {{ include "mychart.fullname" . }}
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {{ include "mychart.fullname" . }}
subjects:
- kind: ServiceAccount
  name: {{ include "mychart.serviceAccountName" . }}
  namespace: {{ .Release.Namespace }}
{{- end }}
```

### 3. Network Policies

```yaml
# templates/networkpolicy.yaml
{{- if .Values.networkPolicy.enabled -}}
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: {{ include "mychart.fullname" . }}
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
spec:
  podSelector:
    matchLabels:
      {{- include "mychart.selectorLabels" . | nindent 6 }}
  policyTypes:
  {{- if .Values.networkPolicy.ingress }}
  - Ingress
  {{- end }}
  {{- if .Values.networkPolicy.egress }}
  - Egress
  {{- end }}
  {{- if .Values.networkPolicy.ingress }}
  ingress:
  - from:
    {{- range .Values.networkPolicy.ingress.from }}
    - {{ toYaml . | nindent 6 }}
    {{- end }}
    ports:
    {{- range .Values.networkPolicy.ingress.ports }}
    - protocol: {{ .protocol }}
      port: {{ .port }}
    {{- end }}
  {{- end }}
  {{- if .Values.networkPolicy.egress }}
  egress:
  - to:
    {{- range .Values.networkPolicy.egress.to }}
    - {{ toYaml . | nindent 6 }}
    {{- end }}
    ports:
    {{- range .Values.networkPolicy.egress.ports }}
    - protocol: {{ .protocol }}
      port: {{ .port }}
    {{- end }}
  {{- end }}
{{- end }}
```

Example values:
```yaml
networkPolicy:
  enabled: true
  ingress:
    from:
    - podSelector:
        matchLabels:
          app: frontend
    - namespaceSelector:
        matchLabels:
          name: production
    ports:
    - protocol: TCP
      port: 8080
  egress:
    to:
    - podSelector:
        matchLabels:
          app: database
    - namespaceSelector:
        matchLabels:
          name: production
    ports:
    - protocol: TCP
      port: 5432
```

### 4. Secret Management

#### Option 1: External Secrets Operator

```yaml
# templates/externalsecret.yaml
{{- if .Values.externalSecrets.enabled -}}
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: {{ include "mychart.fullname" . }}
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
spec:
  secretStoreRef:
    name: {{ .Values.externalSecrets.secretStore }}
    kind: {{ .Values.externalSecrets.secretStoreKind | default "SecretStore" }}
  target:
    name: {{ include "mychart.fullname" . }}-secret
    creationPolicy: Owner
  data:
  {{- range .Values.externalSecrets.data }}
  - secretKey: {{ .secretKey }}
    remoteRef:
      key: {{ .remoteKey }}
      {{- if .property }}
      property: {{ .property }}
      {{- end }}
  {{- end }}
{{- end }}
```

#### Option 2: Sealed Secrets

```yaml
# templates/sealedsecret.yaml
{{- if .Values.sealedSecrets.enabled -}}
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: {{ include "mychart.fullname" . }}
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
spec:
  encryptedData:
    {{- range $key, $value := .Values.sealedSecrets.encryptedData }}
    {{ $key }}: {{ $value }}
    {{- end }}
  template:
    type: {{ .Values.sealedSecrets.type | default "Opaque" }}
{{- end }}
```

#### Option 3: Vault Integration

```yaml
# templates/deployment.yaml with Vault annotations
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "{{ .Values.vault.role }}"
        vault.hashicorp.com/agent-inject-secret-database-config: "{{ .Values.vault.secretPath }}"
        vault.hashicorp.com/agent-inject-template-database-config: |
          {{`{{- with secret "`}}{{ .Values.vault.secretPath }}{{`" -}}
          export DB_USERNAME="{{ .Data.data.username }}"
          export DB_PASSWORD="{{ .Data.data.password }}"
          {{- end -}}`}}
```

### 5. Image Security

```yaml
# values.yaml
image:
  registry: docker.io
  repository: myapp/myimage
  # Prefer digests over tags for immutability
  digest: "sha256:abc123..."
  # Or use specific version tags, never 'latest'
  tag: "1.2.3"
  pullPolicy: IfNotPresent

# Image pull secrets
imagePullSecrets:
  - name: registry-credentials

# Container image verification (with policy controller)
imageVerification:
  enabled: true
  policy: require-signature
  publicKey: |
    -----BEGIN PUBLIC KEY-----
    ...
    -----END PUBLIC KEY-----
```

### 6. Pod Disruption Budget

```yaml
# templates/pdb.yaml
{{- if .Values.podDisruptionBudget.enabled -}}
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ include "mychart.fullname" . }}
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
spec:
  {{- if .Values.podDisruptionBudget.minAvailable }}
  minAvailable: {{ .Values.podDisruptionBudget.minAvailable }}
  {{- end }}
  {{- if .Values.podDisruptionBudget.maxUnavailable }}
  maxUnavailable: {{ .Values.podDisruptionBudget.maxUnavailable }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "mychart.selectorLabels" . | nindent 6 }}
{{- end }}
```

## Part 2: GPG Chart Signing

### Setup GPG

```bash
# Generate GPG key
gpg --full-generate-key
# Choose:
# - RSA and RSA
# - 4096 bits
# - No expiration (or set expiration)
# - Real name and email

# List keys
gpg --list-keys

# Export public key
gpg --armor --export your-email@example.com > pubkey.asc

# Export private key (keep secure!)
gpg --armor --export-secret-keys your-email@example.com > private-key.asc
```

### Sign a Chart

```bash
# Package and sign
helm package mychart/
helm package --sign --key 'Your Name' --keyring ~/.gnupg/secring.gpg mychart/

# Or sign after packaging
helm package mychart/
gpg --detach-sign --armor mychart-1.0.0.tgz

# This creates:
# - mychart-1.0.0.tgz (chart package)
# - mychart-1.0.0.tgz.prov (provenance file)
```

### Provenance File

The `.prov` file contains:
- Chart metadata (Chart.yaml)
- Hashes of chart files
- GPG signature

Example structure:
```
-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA512

apiVersion: v2
appVersion: 1.0.0
description: A Helm chart for Kubernetes
name: mychart
type: application
version: 1.0.0

...
files:
  mychart-1.0.0.tgz: sha256:abc123...

-----BEGIN PGP SIGNATURE-----
...
-----END PGP SIGNATURE-----
```

### Verify a Chart

```bash
# Add public key to keyring
gpg --import pubkey.asc

# Verify chart
helm verify mychart-1.0.0.tgz

# Install with verification
helm install my-release mychart-1.0.0.tgz --verify

# Verify from repository
helm install my-release myrepo/mychart --verify
```

### CI/CD Signing

#### GitHub Actions

```yaml
name: Sign and Release Chart

on:
  push:
    tags:
      - 'v*'

jobs:
  sign-release:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Import GPG key
        run: |
          echo "${{ secrets.GPG_PRIVATE_KEY }}" | gpg --import
          echo "${{ secrets.GPG_PASSPHRASE }}" | gpg --batch --yes --passphrase-fd 0 --quick-add-uid $(gpg --list-keys --with-colons | awk -F: '/^pub/ {print $5}') "Build Bot <bot@example.com>"

      - name: Package and sign chart
        run: |
          helm package --sign --key 'Build Bot' --keyring ~/.gnupg/secring.gpg charts/mychart/

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: signed-chart
          path: |
            mychart-*.tgz
            mychart-*.tgz.prov
```

## Part 3: OCI Registry Operations

### Registry Authentication

#### Docker Hub

```bash
# Login
helm registry login registry-1.docker.io \
  --username your-username

# Or with token
echo $DOCKER_TOKEN | helm registry login registry-1.docker.io \
  --username your-username \
  --password-stdin
```

#### Amazon ECR

```bash
# Get login password
aws ecr get-login-password --region us-west-2 | \
  helm registry login \
  --username AWS \
  --password-stdin \
  123456789012.dkr.ecr.us-west-2.amazonaws.com

# Create repository (first time)
aws ecr create-repository --repository-name charts/mychart --region us-west-2
```

#### Google Artifact Registry

```bash
# Login with gcloud
gcloud auth configure-docker us-central1-docker.pkg.dev

# Or with access token
gcloud auth print-access-token | \
  helm registry login \
  --username oauth2accesstoken \
  --password-stdin \
  us-central1-docker.pkg.dev

# Create repository (first time)
gcloud artifacts repositories create charts \
  --repository-format=docker \
  --location=us-central1
```

#### Azure Container Registry

```bash
# Login with Azure CLI
az acr login --name myregistry

# Or with token
az acr login --name myregistry --username $USERNAME --password $PASSWORD

# Or with managed identity
az acr login --name myregistry --identity

# Create repository (automatic on first push)
```

#### Harbor

```bash
# Login
helm registry login harbor.example.com \
  --username admin

# With robot account
helm registry login harbor.example.com \
  --username 'robot$myrobot' \
  --password-stdin < robot-token.txt
```

#### GitHub Container Registry (GHCR)

```bash
# Login with PAT (Personal Access Token)
echo $GITHUB_TOKEN | helm registry login ghcr.io \
  --username your-username \
  --password-stdin

# Token needs: write:packages, read:packages, delete:packages permissions
```

### Push Charts to OCI Registry

```bash
# Package chart
helm package mychart/

# Push to registry
helm push mychart-1.0.0.tgz oci://registry.example.com/charts

# Push to specific path
helm push mychart-1.0.0.tgz oci://registry.example.com/myorg/charts

# Examples for different registries:
# Docker Hub
helm push mychart-1.0.0.tgz oci://registry-1.docker.io/yourusername

# ECR
helm push mychart-1.0.0.tgz oci://123456789012.dkr.ecr.us-west-2.amazonaws.com/charts

# GCR/Artifact Registry
helm push mychart-1.0.0.tgz oci://us-central1-docker.pkg.dev/project-id/charts

# ACR
helm push mychart-1.0.0.tgz oci://myregistry.azurecr.io/charts

# Harbor
helm push mychart-1.0.0.tgz oci://harbor.example.com/library/charts

# GHCR
helm push mychart-1.0.0.tgz oci://ghcr.io/username/charts
```

### Pull and Install from OCI

```bash
# Pull chart
helm pull oci://registry.example.com/charts/mychart --version 1.0.0

# Untar pulled chart
helm pull oci://registry.example.com/charts/mychart --version 1.0.0 --untar

# Install directly
helm install my-release oci://registry.example.com/charts/mychart --version 1.0.0

# Install with values
helm install my-release oci://registry.example.com/charts/mychart \
  --version 1.0.0 \
  -f values.yaml

# Upgrade
helm upgrade my-release oci://registry.example.com/charts/mychart --version 1.1.0
```

### OCI Chart Dependencies

```yaml
# Chart.yaml
dependencies:
  - name: postgresql
    version: "12.1.0"
    repository: "oci://registry-1.docker.io/bitnamicharts"

  - name: redis
    version: "17.0.0"
    repository: "oci://registry.example.com/charts"
    condition: redis.enabled

  - name: mychart
    version: "1.0.0"
    repository: "oci://123456789012.dkr.ecr.us-west-2.amazonaws.com/charts"
```

Update dependencies:
```bash
# Authenticate to all required registries first
helm registry login registry-1.docker.io
helm registry login registry.example.com

# Update dependencies
helm dependency update mychart/

# Build dependencies
helm dependency build mychart/
```

### List Registry Contents

```bash
# Show all tags for a chart
helm show chart oci://registry.example.com/charts/mychart --version 1.0.0

# Using registry CLI tools
# Docker Hub
curl -s https://hub.docker.com/v2/repositories/yourusername/mychart/tags | jq

# ECR
aws ecr list-images --repository-name charts/mychart --region us-west-2

# GCR
gcloud artifacts docker tags list us-central1-docker.pkg.dev/project-id/charts/mychart

# ACR
az acr repository show-tags --name myregistry --repository charts/mychart

# Harbor
curl -u admin:password https://harbor.example.com/api/v2.0/projects/library/repositories/mychart/artifacts
```

### OCI Chart Signing (Cosign/Sigstore)

#### Install Cosign

```bash
# macOS
brew install cosign

# Linux
curl -LO https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64
sudo mv cosign-linux-amd64 /usr/local/bin/cosign
sudo chmod +x /usr/local/bin/cosign
```

#### Generate Key Pair

```bash
# Generate keys
cosign generate-key-pair

# Creates:
# - cosign.key (private key)
# - cosign.pub (public key)
```

#### Sign OCI Chart

```bash
# Package and push chart
helm package mychart/
helm push mychart-1.0.0.tgz oci://registry.example.com/charts

# Sign the chart
cosign sign --key cosign.key \
  registry.example.com/charts/mychart:1.0.0

# Sign with annotations
cosign sign --key cosign.key \
  -a author=john@example.com \
  -a build-id=12345 \
  registry.example.com/charts/mychart:1.0.0

# Keyless signing (with OIDC)
cosign sign registry.example.com/charts/mychart:1.0.0
```

#### Verify OCI Chart

```bash
# Verify with public key
cosign verify --key cosign.pub \
  registry.example.com/charts/mychart:1.0.0

# Verify keyless signature
cosign verify registry.example.com/charts/mychart:1.0.0 \
  --certificate-identity=john@example.com \
  --certificate-oidc-issuer=https://accounts.google.com
```

#### Attach SBOMs

```bash
# Generate SBOM
syft packages oci-archive:mychart-1.0.0.tgz -o spdx-json > sbom.spdx.json

# Attach SBOM
cosign attach sbom --sbom sbom.spdx.json \
  registry.example.com/charts/mychart:1.0.0

# Verify SBOM
cosign verify-attestation --key cosign.pub \
  --type spdxjson \
  registry.example.com/charts/mychart:1.0.0
```

## Part 4: Migration to OCI

### Classic Repository to OCI Migration

#### 1. Assess Current Setup

```bash
# List current repos
helm repo list

# Download all charts
for repo in $(helm repo list -o json | jq -r '.[].name'); do
  for chart in $(helm search repo $repo -o json | jq -r '.[].name'); do
    helm pull $chart
  done
done
```

#### 2. Push to OCI Registry

```bash
#!/bin/bash
# migrate-to-oci.sh

OCI_REGISTRY="registry.example.com/charts"

# Package and push all charts
for chart_dir in charts/*/; do
  chart_name=$(basename "$chart_dir")

  # Package
  helm package "$chart_dir"

  # Get version
  version=$(helm show chart "$chart_dir" | grep '^version:' | awk '{print $2}')

  # Push
  helm push "${chart_name}-${version}.tgz" "oci://${OCI_REGISTRY}"

  echo "Migrated $chart_name:$version"
done
```

#### 3. Update Dependencies

Old:
```yaml
dependencies:
  - name: postgresql
    version: "12.1.0"
    repository: "https://charts.bitnami.com/bitnami"
```

New:
```yaml
dependencies:
  - name: postgresql
    version: "12.1.0"
    repository: "oci://registry-1.docker.io/bitnamicharts"
```

#### 4. Update CI/CD

Old:
```bash
helm repo add myrepo https://charts.example.com
helm repo update
helm upgrade my-release myrepo/mychart
```

New:
```bash
helm registry login registry.example.com
helm upgrade my-release oci://registry.example.com/charts/mychart --version 1.0.0
```

## Part 5: Security Checklist

### Chart Security Checklist

- [ ] Security contexts configured (pod and container level)
- [ ] Non-root user specified
- [ ] Read-only root filesystem
- [ ] No privileged containers
- [ ] Capabilities dropped
- [ ] Seccomp profile configured
- [ ] Resource limits defined
- [ ] RBAC properly scoped
- [ ] Network policies defined
- [ ] Secrets management solution implemented
- [ ] Image digests used (not 'latest' tags)
- [ ] Image pull policies configured
- [ ] PodDisruptionBudget defined
- [ ] No hardcoded secrets in values
- [ ] Ingress TLS configured
- [ ] Service account automount controlled

### Supply Chain Security

- [ ] Charts signed with GPG or Cosign
- [ ] Provenance files generated
- [ ] SBOM attached to charts
- [ ] Vulnerability scanning in CI/CD
- [ ] Image scanning configured
- [ ] Dependencies pinned to specific versions
- [ ] OCI registry with authentication
- [ ] Access controls on registry
- [ ] Audit logging enabled
- [ ] Regular security updates

---

**Remember**: Security is not a feature, it's a requirement. Always implement defense in depth!
