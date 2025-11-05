# Helm Best Practices Reference

Comprehensive guide to Helm chart development best practices, template functions, patterns, and versioning.

## Template Functions Reference

### String Functions

```yaml
# toYaml - Convert object to YAML
resources:
  {{- toYaml .Values.resources | nindent 2 }}

# quote - Add double quotes
image: {{ .Values.image.repository | quote }}

# squote - Add single quotes
command: {{ .Values.command | squote }}

# upper/lower/title
name: {{ .Values.name | upper }}

# trim/trimPrefix/trimSuffix
value: {{ .Values.value | trim }}

# replace
url: {{ .Values.url | replace "http://" "https://" }}

# cat - Concatenate strings
fullname: {{ .Release.Name | cat "-" .Chart.Name }}

# substr - Extract substring
short: {{ .Values.longName | substr 0 5 }}
```

### Default and Required Values

```yaml
# default - Provide fallback value
replicas: {{ .Values.replicaCount | default 1 }}

# required - Make value mandatory
apiKey: {{ required "API key is required" .Values.apiKey }}

# empty - Check if value is empty
{{- if not (empty .Values.config) }}
# Use config
{{- end }}
```

### Type Conversion

```yaml
# toString
value: {{ .Values.number | toString | quote }}

# toJson - Convert to JSON
data:
  config.json: {{ .Values.config | toJson | quote }}

# fromYaml - Parse YAML string
{{- $config := .Values.yamlString | fromYaml }}

# toToml - Convert to TOML
config.toml: {{ .Values.config | toToml | quote }}

# b64enc/b64dec - Base64 encoding
password: {{ .Values.password | b64enc | quote }}
```

### List Functions

```yaml
# list - Create list
tags: {{ list "prod" "web" "v1" }}

# append - Add to list
allTags: {{ .Values.tags | append "latest" }}

# has - Check if item exists
{{- if has "prod" .Values.tags }}

# first/rest/last - List operations
firstTag: {{ .Values.tags | first }}
remainingTags: {{ .Values.tags | rest }}

# uniq - Remove duplicates
uniqueTags: {{ .Values.tags | uniq }}

# without - Remove items
filtered: {{ .Values.tags | without "dev" "test" }}

# sortAlpha - Sort alphabetically
sorted: {{ .Values.tags | sortAlpha }}
```

### Dictionary (Map) Functions

```yaml
# dict - Create dictionary
{{- $myDict := dict "key1" "value1" "key2" "value2" }}

# set - Add key-value
{{- $_ := set $myDict "key3" "value3" }}

# unset - Remove key
{{- $_ := unset $myDict "key1" }}

# hasKey - Check if key exists
{{- if hasKey .Values "feature" }}

# pluck - Extract values from multiple dicts
names: {{ pluck "name" .Values.users | compact | uniq }}

# merge/mergeOverwrite - Combine dictionaries
{{- $merged := merge .Values.defaults .Values.overrides }}

# keys - Get all keys
{{- range $key := keys .Values.config | sortAlpha }}

# values - Get all values
{{- range $val := values .Values.config }}

# pick/omit - Select or exclude keys
{{- $subset := pick .Values "key1" "key2" }}
{{- $without := omit .Values "secret" "password" }}
```

### Flow Control

```yaml
# if/else
{{- if .Values.enabled }}
enabled: true
{{- else }}
enabled: false
{{- end }}

# with - Change scope
{{- with .Values.database }}
host: {{ .host }}
port: {{ .port }}
{{- end }}

# range - Iterate
{{- range .Values.items }}
- {{ . }}
{{- end }}

# range with index
{{- range $index, $item := .Values.items }}
- index: {{ $index }}
  value: {{ $item }}
{{- end }}

# range over map
{{- range $key, $value := .Values.config }}
{{ $key }}: {{ $value }}
{{- end }}
```

### Indentation

```yaml
# nindent - Newline then indent (RECOMMENDED)
env:
  {{- toYaml .Values.env | nindent 2 }}

# indent - Indent without newline
labels:
  {{ toYaml .Values.labels | indent 2 }}

# Common indentation levels
# 2 spaces: YAML list items, dictionary values
# 4 spaces: Nested structures
# 8-12 spaces: Deeply nested structures
```

### Template Inclusion

```yaml
# include - Include named template
labels:
  {{- include "mychart.labels" . | nindent 2 }}

# template - Include template (deprecated, use include)
{{ template "mychart.name" . }}

# tpl - Render string as template
value: {{ tpl .Values.dynamicValue . }}
```

### Lookup Function (Runtime Queries)

```yaml
# lookup - Query Kubernetes API during install/upgrade
{{- $secret := lookup "v1" "Secret" .Release.Namespace "mysecret" }}
{{- if $secret }}
# Secret exists, use it
password: {{ $secret.data.password }}
{{- else }}
# Secret doesn't exist, create new
password: {{ randAlphaNum 16 | b64enc }}
{{- end }}

# Check if resource exists
{{- $existing := lookup "apps/v1" "Deployment" .Release.Namespace (include "mychart.fullname" .) }}
{{- if $existing }}
# Preserve certain fields from existing deployment
replicas: {{ $existing.spec.replicas }}
{{- end }}
```

### Cryptographic and Random Functions

```yaml
# Random strings
password: {{ randAlphaNum 16 }}
token: {{ randAlpha 32 }}
id: {{ uuidv4 }}

# Hashing
checksum: {{ .Values.config | sha256sum }}
hash: {{ .Values.data | sha1sum }}

# Generate random in range
port: {{ randInt 30000 32767 }}
```

### Date Functions

```yaml
# now - Current timestamp
timestamp: {{ now | date "2006-01-02T15:04:05Z07:00" }}

# Date formatting
created: {{ now | date "2006-01-02" }}
time: {{ now | date "15:04:05" }}

# Unix timestamp
epoch: {{ now | unixEpoch }}

# Date arithmetic
future: {{ now | dateModify "+24h" }}
past: {{ now | dateModify "-7d" }}
```

### Regular Expressions

```yaml
# regexMatch - Test if matches
{{- if regexMatch "^[a-z]+$" .Values.name }}

# regexFind - Find first match
found: {{ regexFind "[0-9]+" .Values.version }}

# regexFindAll - Find all matches
numbers: {{ regexFindAll "[0-9]+" .Values.text -1 }}

# regexReplaceAll - Replace matches
cleaned: {{ regexReplaceAll "[^a-z0-9]" .Values.name "" }}

# regexSplit - Split by regex
parts: {{ regexSplit "-" .Values.name -1 }}
```

### URL Functions

```yaml
# urlParse - Parse URL
{{- $url := urlParse "https://example.com:8080/path?query=value" }}
host: {{ $url.host }}
port: {{ $url.port }}
path: {{ $url.path }}

# urlJoin - Join URL components
url: {{ dict "scheme" "https" "host" "example.com" "path" "/api" | urlJoin }}
```

### Kubernetes Functions

```yaml
# toYaml - Most important for K8s resources
resources:
  {{- toYaml .Values.resources | nindent 2 }}

# Common pattern for optional blocks
{{- if .Values.tolerations }}
tolerations:
  {{- toYaml .Values.tolerations | nindent 2 }}
{{- end }}

# Affinity rules
{{- if .Values.affinity }}
affinity:
  {{- toYaml .Values.affinity | nindent 2 }}
{{- end }}
```

## Chart Structure Best Practices

### Recommended Directory Layout

```
mychart/
├── Chart.yaml                 # Required: Chart metadata
├── Chart.lock                 # Generated: Dependency lock file
├── values.yaml                # Required: Default values
├── values.schema.json         # Recommended: JSON schema validation
├── README.md                  # Recommended: Chart documentation
├── LICENSE                    # Recommended: License file
├── .helmignore               # Optional: Files to exclude
├── templates/
│   ├── NOTES.txt             # Recommended: Post-install notes
│   ├── _helpers.tpl          # Recommended: Template helpers
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── serviceaccount.yaml
│   ├── configmap.yaml
│   ├── secret.yaml           # Be cautious with secrets
│   ├── ingress.yaml
│   ├── hpa.yaml             # Horizontal Pod Autoscaler
│   ├── pdb.yaml             # Pod Disruption Budget
│   ├── networkpolicy.yaml
│   ├── tests/
│   │   └── test-connection.yaml
│   └── hooks/
│       ├── pre-install-job.yaml
│       └── post-upgrade-job.yaml
├── charts/                    # Dependency charts (if not using Chart.lock)
├── crds/                     # Custom Resource Definitions
│   └── mycrd.yaml
└── ci/                       # CI test values
    ├── default-values.yaml
    └── production-values.yaml
```

### Chart.yaml Structure

```yaml
apiVersion: v2
name: mychart
description: A Helm chart for Kubernetes
type: application  # or 'library' for shared templates
version: 1.0.0  # Chart version (SemVer)
appVersion: "2.1.0"  # Application version

# Optional but recommended
keywords:
  - web
  - application
home: https://example.com
sources:
  - https://github.com/example/repo
maintainers:
  - name: John Doe
    email: john@example.com
    url: https://github.com/johndoe
icon: https://example.com/icon.png

# Dependencies
dependencies:
  - name: postgresql
    version: "12.1.0"
    repository: "https://charts.bitnami.com/bitnami"
    condition: postgresql.enabled
    tags:
      - database
  - name: redis
    version: "17.0.0"
    repository: "oci://registry-1.docker.io/bitnamicharts"
    condition: redis.enabled

# Kubernetes version constraint
kubeVersion: ">=1.24.0-0"

# Annotations
annotations:
  category: Web
  licenses: Apache-2.0
```

### values.yaml Best Practices

```yaml
# Global values (for subcharts)
global:
  imageRegistry: ""
  imagePullSecrets: []
  storageClass: ""

# Image configuration
image:
  registry: docker.io
  repository: myapp/myimage
  tag: "1.0.0"  # Avoid 'latest'
  digest: ""  # More secure than tag
  pullPolicy: IfNotPresent
  pullSecrets: []

# Deployment configuration
replicaCount: 1

# Update strategy
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0

# Service account
serviceAccount:
  create: true
  automount: true
  annotations: {}
  name: ""

# Security context (pod level)
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault

# Security context (container level)
securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1000

# Service configuration
service:
  type: ClusterIP
  port: 80
  targetPort: http
  annotations: {}
  labels: {}

# Ingress configuration
ingress:
  enabled: false
  className: "nginx"
  annotations: {}
    # cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: chart-example.local
      paths:
        - path: /
          pathType: Prefix
  tls: []
    # - secretName: chart-example-tls
    #   hosts:
    #     - chart-example.local

# Resources (ALWAYS SPECIFY)
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 100m
    memory: 128Mi

# Autoscaling
autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80

# Probes
livenessProbe:
  enabled: true
  httpGet:
    path: /healthz
    port: http
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  enabled: true
  httpGet:
    path: /ready
    port: http
  initialDelaySeconds: 5
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

# Node selection
nodeSelector: {}
tolerations: []
affinity: {}

# Pod placement
topologySpreadConstraints: []

# Volumes
persistence:
  enabled: false
  storageClass: ""
  accessMode: ReadWriteOnce
  size: 8Gi
  annotations: {}

# ConfigMap data
config: {}

# Secret data (use external secrets in production!)
secrets: {}

# Extra environment variables
extraEnv: []
extraEnvFrom: []

# Pod annotations and labels
podAnnotations: {}
podLabels: {}

# Priority class
priorityClassName: ""

# Network policy
networkPolicy:
  enabled: false
  policyTypes:
    - Ingress
    - Egress

# Pod disruption budget
podDisruptionBudget:
  enabled: false
  minAvailable: 1
  # maxUnavailable: 1

# Testing
tests:
  enabled: true
```

### _helpers.tpl Template Library

```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "mychart.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "mychart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "mychart.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "mychart.labels" -}}
helm.sh/chart: {{ include "mychart.chart" . }}
{{ include "mychart.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "mychart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mychart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "mychart.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "mychart.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Return the proper image name
*/}}
{{- define "mychart.image" -}}
{{- $registry := .Values.image.registry -}}
{{- $repository := .Values.image.repository -}}
{{- $tag := .Values.image.tag | toString -}}
{{- if .Values.image.digest }}
{{- printf "%s/%s@%s" $registry $repository .Values.image.digest }}
{{- else }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- end }}
{{- end }}

{{/*
Return the proper Docker Image Registry Secret Names
*/}}
{{- define "mychart.imagePullSecrets" -}}
{{- if .Values.global.imagePullSecrets }}
{{- range .Values.global.imagePullSecrets }}
- name: {{ . }}
{{- end }}
{{- else if .Values.image.pullSecrets }}
{{- range .Values.image.pullSecrets }}
- name: {{ . }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Renders a value that contains template.
Usage:
{{ include "mychart.tplvalues.render" ( dict "value" .Values.path.to.value "context" $) }}
*/}}
{{- define "mychart.tplvalues.render" -}}
{{- if typeIs "string" .value }}
{{- tpl .value .context }}
{{- else }}
{{- tpl (.value | toYaml) .context }}
{{- end }}
{{- end }}
```

## Versioning Strategy

### Semantic Versioning (SemVer)

**Chart Version** (`version` in Chart.yaml):
- Format: `MAJOR.MINOR.PATCH`
- `MAJOR`: Breaking changes (incompatible API changes)
- `MINOR`: New features (backward-compatible)
- `PATCH`: Bug fixes (backward-compatible)

**App Version** (`appVersion` in Chart.yaml):
- The version of the application being deployed
- Not required to follow SemVer
- Should match the actual application version

### When to Bump Versions

**MAJOR (1.0.0 → 2.0.0)**:
- Removing values
- Changing value types
- Renaming resources
- Changing defaults that break existing deployments
- Upgrading to incompatible CRD versions

**MINOR (1.0.0 → 1.1.0)**:
- Adding new values
- Adding new optional resources
- Adding new features
- Non-breaking enhancements

**PATCH (1.0.0 → 1.0.1)**:
- Bug fixes
- Documentation updates
- Security patches
- Performance improvements

### Version Constraints

In `Chart.yaml` dependencies:

```yaml
dependencies:
  # Exact version
  - name: postgresql
    version: "12.1.0"
    repository: "https://charts.bitnami.com/bitnami"

  # Range constraints
  - name: redis
    version: ">=17.0.0 <18.0.0"  # Allow minor/patch updates
    repository: "oci://registry-1.docker.io/bitnamicharts"

  # Caret (compatible)
  - name: mongodb
    version: "^13.0.0"  # Allows >=13.0.0 <14.0.0
    repository: "https://charts.bitnami.com/bitnami"

  # Tilde (patch updates)
  - name: mysql
    version: "~9.3.0"  # Allows >=9.3.0 <9.4.0
    repository: "https://charts.bitnami.com/bitnami"
```

## Performance Optimization

### Template Rendering

**Avoid**:
```yaml
# Slow: Multiple template calls
labels:
  app: {{ template "mychart.name" . }}
  version: {{ template "mychart.version" . }}
  chart: {{ template "mychart.chart" . }}
```

**Prefer**:
```yaml
# Fast: Single template call with all labels
labels:
  {{- include "mychart.labels" . | nindent 2 }}
```

### Resource Limits

Always specify resource limits to prevent resource starvation:

```yaml
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

### Image Pull Policy

```yaml
# Faster for development
pullPolicy: IfNotPresent

# More secure for production
pullPolicy: Always

# Best practice: Use digests
image:
  repository: myapp/myimage
  digest: sha256:abc123...
  pullPolicy: IfNotPresent
```

## Common Patterns

### Multi-Container Pods

```yaml
spec:
  containers:
  - name: {{ .Chart.Name }}
    image: {{ include "mychart.image" . }}
    # Main container config

  {{- if .Values.sidecar.enabled }}
  - name: sidecar
    image: {{ .Values.sidecar.image }}
    # Sidecar config
  {{- end }}

  {{- range .Values.extraContainers }}
  - {{ toYaml . | nindent 2 }}
  {{- end }}
```

### Init Containers

```yaml
{{- if .Values.initContainers }}
initContainers:
  {{- toYaml .Values.initContainers | nindent 2 }}
{{- end }}
```

### Environment Variables from Multiple Sources

```yaml
env:
  - name: POD_NAME
    valueFrom:
      fieldRef:
        fieldPath: metadata.name
  - name: POD_NAMESPACE
    valueFrom:
      fieldRef:
        fieldPath: metadata.namespace
  {{- range .Values.env }}
  - {{ toYaml . | nindent 2 }}
  {{- end }}

{{- if .Values.envFrom }}
envFrom:
  {{- toYaml .Values.envFrom | nindent 2 }}
{{- end }}
```

### Conditional Resources

```yaml
{{- if and .Values.ingress.enabled .Values.ingress.tls }}
# TLS-enabled ingress
{{- else if .Values.ingress.enabled }}
# Non-TLS ingress
{{- end }}
```

### Merging Annotations

```yaml
annotations:
  {{- if .Values.podAnnotations }}
  {{- toYaml .Values.podAnnotations | nindent 2 }}
  {{- end }}
  {{- if .Values.metrics.enabled }}
  prometheus.io/scrape: "true"
  prometheus.io/port: {{ .Values.metrics.port | quote }}
  {{- end }}
```

## Documentation

### NOTES.txt Template

```
CHART NAME: {{ .Chart.Name }}
CHART VERSION: {{ .Chart.Version }}
APP VERSION: {{ .Chart.AppVersion }}

** Please be patient while the chart is being deployed **

{{- if .Values.ingress.enabled }}

1. Get the application URL by running:

{{- range $host := .Values.ingress.hosts }}
  http{{ if $.Values.ingress.tls }}s{{ end }}://{{ $host.host }}{{ (index $host.paths 0).path }}
{{- end }}

{{- else if contains "NodePort" .Values.service.type }}

1. Get the application URL by running:

  export NODE_PORT=$(kubectl get --namespace {{ .Release.Namespace }} -o jsonpath="{.spec.ports[0].nodePort}" services {{ include "mychart.fullname" . }})
  export NODE_IP=$(kubectl get nodes --namespace {{ .Release.Namespace }} -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT

{{- else if contains "LoadBalancer" .Values.service.type }}

1. Get the application URL by running:

  NOTE: It may take a few minutes for the LoadBalancer IP to be available.

  export SERVICE_IP=$(kubectl get svc --namespace {{ .Release.Namespace }} {{ include "mychart.fullname" . }} --template "{{"{{ range (index .status.loadBalancer.ingress 0) }}{{.}}{{ end }}"}}")
  echo http://$SERVICE_IP:{{ .Values.service.port }}

{{- else }}

1. Get the application URL by running:

  kubectl --namespace {{ .Release.Namespace }} port-forward svc/{{ include "mychart.fullname" . }} 8080:{{ .Values.service.port }}
  echo "Visit http://127.0.0.1:8080"

{{- end }}

{{- if .Values.postgresql.enabled }}

2. Get the PostgreSQL password:

  export POSTGRES_PASSWORD=$(kubectl get secret --namespace {{ .Release.Namespace }} {{ .Release.Name }}-postgresql -o jsonpath="{.data.postgres-password}" | base64 -d)

{{- end }}

{{- if not .Values.existingSecret }}

WARNING: You are using chart-generated secrets. In production, use an external secret management solution.

{{- end }}
```

### README.md Structure

```markdown
# Chart Name

Brief description of what this chart deploys.

## TL;DR

```bash
helm repo add myrepo https://charts.example.com
helm install my-release myrepo/mychart
```

## Introduction

Detailed description, features, architecture.

## Prerequisites

- Kubernetes 1.24+
- Helm 3.8+
- PV provisioner support (for persistence)

## Installing the Chart

```bash
helm install my-release myrepo/mychart --set key=value
```

## Uninstalling the Chart

```bash
helm uninstall my-release
```

## Parameters

### Global Parameters

| Name | Description | Value |
|------|-------------|-------|
| `global.imageRegistry` | Global Docker image registry | `""` |

### Common Parameters

| Name | Description | Value |
|------|-------------|-------|
| `replicaCount` | Number of replicas | `1` |
| `image.repository` | Image repository | `myapp/image` |

### Security Parameters

...

## Configuration Examples

### High Availability Setup

```yaml
replicaCount: 3
podDisruptionBudget:
  enabled: true
  minAvailable: 2
```

### Production Setup

...

## Upgrading

### To 2.0.0

Breaking changes:
- ...

## License

Copyright © 2025
```

---

**Tip**: Bookmark this reference for quick access to template functions and patterns!
