# Testing and Validation Reference

Comprehensive guide to testing Helm charts with various tools and strategies.

## Testing Pyramid

```
        ┌──────────────────┐
        │  Integration     │  Slow, High Confidence
        │  Testing         │  (Real cluster)
        ├──────────────────┤
        │  Manifest        │  Medium Speed
        │  Validation      │  (kubeconform/kubeval)
        ├──────────────────┤
        │  Unit Testing    │  Fast
        │  (helm-unittest) │
        ├──────────────────┤
        │  Linting         │  Very Fast
        │  (helm lint, ct) │
        └──────────────────┘
```

## 1. Linting

### Basic Helm Lint

```bash
# Lint a chart
helm lint mychart/

# Lint with custom values
helm lint mychart/ -f mychart/ci/test-values.yaml

# Lint with strict mode
helm lint mychart/ --strict

# Lint with set values
helm lint mychart/ --set replicaCount=3
```

### Chart Testing (ct)

Install:
```bash
# Using binary
curl -sSL https://github.com/helm/chart-testing/releases/download/v3.10.0/chart-testing_3.10.0_linux_amd64.tar.gz | tar xz
sudo mv ct /usr/local/bin/

# Using pip
pip install yamllint yamale
```

Configuration (`ct.yaml`):
```yaml
# ct.yaml
remote: origin
target-branch: main
chart-dirs:
  - charts
chart-repos:
  - bitnami=https://charts.bitnami.com/bitnami
helm-extra-args: --timeout 600s
check-version-increment: true
validate-maintainers: true
```

Usage:
```bash
# Lint changed charts
ct lint --config ct.yaml

# Lint all charts
ct lint --all --config ct.yaml

# Install and test charts
ct install --config ct.yaml

# List changed charts
ct list-changed --config ct.yaml
```

### Yamllint Configuration

`.yamllint`:
```yaml
extends: default

rules:
  line-length:
    max: 120
    level: warning
  indentation:
    spaces: 2
    indent-sequences: true
  comments:
    min-spaces-from-content: 1
  comments-indentation: {}
  document-start: disable
  truthy:
    allowed-values: ['true', 'false', 'yes', 'no']
```

## 2. Schema Validation

### values.schema.json

Create JSON schema for values validation:

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["image", "service"],
  "properties": {
    "replicaCount": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10,
      "description": "Number of replicas"
    },
    "image": {
      "type": "object",
      "required": ["repository", "tag"],
      "properties": {
        "repository": {
          "type": "string",
          "description": "Image repository"
        },
        "tag": {
          "type": "string",
          "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$",
          "description": "Image tag (must be semantic version)"
        },
        "pullPolicy": {
          "type": "string",
          "enum": ["Always", "IfNotPresent", "Never"],
          "description": "Image pull policy"
        }
      }
    },
    "service": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string",
          "enum": ["ClusterIP", "NodePort", "LoadBalancer"],
          "description": "Service type"
        },
        "port": {
          "type": "integer",
          "minimum": 1,
          "maximum": 65535,
          "description": "Service port"
        }
      }
    },
    "resources": {
      "type": "object",
      "properties": {
        "limits": {
          "type": "object",
          "properties": {
            "cpu": {"type": "string"},
            "memory": {"type": "string"}
          }
        },
        "requests": {
          "type": "object",
          "properties": {
            "cpu": {"type": "string"},
            "memory": {"type": "string"}
          }
        }
      }
    },
    "ingress": {
      "type": "object",
      "properties": {
        "enabled": {"type": "boolean"},
        "className": {"type": "string"},
        "hosts": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["host"],
            "properties": {
              "host": {
                "type": "string",
                "format": "hostname"
              },
              "paths": {
                "type": "array",
                "items": {
                  "type": "object",
                  "required": ["path", "pathType"],
                  "properties": {
                    "path": {"type": "string"},
                    "pathType": {
                      "type": "string",
                      "enum": ["Prefix", "Exact", "ImplementationSpecific"]
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

Test schema:
```bash
# Schema is automatically validated during:
helm install --dry-run my-release ./mychart
helm lint ./mychart
helm template ./mychart
```

## 3. Unit Testing with helm-unittest

### Installation

```bash
# Install plugin
helm plugin install https://github.com/helm-unittest/helm-unittest

# Verify installation
helm unittest --help
```

### Test File Structure

`tests/deployment_test.yaml`:
```yaml
suite: test deployment
templates:
  - deployment.yaml
tests:
  - it: should create deployment with correct name
    asserts:
      - isKind:
          of: Deployment
      - equal:
          path: metadata.name
          value: RELEASE-NAME-mychart

  - it: should set replicas from values
    set:
      replicaCount: 3
    asserts:
      - equal:
          path: spec.replicas
          value: 3

  - it: should use correct image
    set:
      image:
        repository: myrepo/myapp
        tag: "1.2.3"
    asserts:
      - equal:
          path: spec.template.spec.containers[0].image
          value: myrepo/myapp:1.2.3

  - it: should set resource limits
    set:
      resources:
        limits:
          cpu: 200m
          memory: 256Mi
    asserts:
      - equal:
          path: spec.template.spec.containers[0].resources.limits.cpu
          value: 200m
      - equal:
          path: spec.template.spec.containers[0].resources.limits.memory
          value: 256Mi

  - it: should add security context when enabled
    set:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
    asserts:
      - equal:
          path: spec.template.spec.securityContext.runAsNonRoot
          value: true
      - equal:
          path: spec.template.spec.securityContext.runAsUser
          value: 1000

  - it: should not create deployment when disabled
    set:
      enabled: false
    asserts:
      - hasDocuments:
          count: 0
```

### Assert Types

```yaml
# Document assertions
- hasDocuments:
    count: 1

- isKind:
    of: Deployment

- isAPIVersion:
    of: apps/v1

- isNullOrEmpty:
    path: metadata.annotations

- isNotEmpty:
    path: spec.template.spec.containers

# Value assertions
- equal:
    path: metadata.name
    value: my-release

- notEqual:
    path: spec.replicas
    value: 0

- matchRegex:
    path: metadata.name
    pattern: ^[a-z-]+$

- contains:
    path: spec.template.spec.containers[0].env
    content:
      name: MY_VAR
      value: my-value

- notContains:
    path: spec.template.metadata.labels
    content:
      test: label

# Snapshot testing
- matchSnapshot:
    path: spec

# Length assertions
- lengthEqual:
    path: spec.template.spec.containers
    count: 1

- isEmpty:
    path: spec.template.spec.initContainers

# Existence assertions
- exists:
    path: spec.template.spec.securityContext

- notExists:
    path: spec.template.spec.hostNetwork

# Boolean assertions
- isTrue:
    path: spec.template.spec.securityContext.runAsNonRoot

- isFalse:
    path: spec.template.spec.hostNetwork

# Null assertions
- isNull:
    path: spec.template.spec.serviceAccountName

- isNotNull:
    path: metadata.labels

# Subset assertions
- isSubset:
    path: metadata.labels
    content:
      app: myapp
```

### Test with Values Files

```yaml
suite: test with custom values
templates:
  - deployment.yaml
values:
  - ../values.yaml
  - ./test-values.yaml
tests:
  - it: should work with production values
    values:
      - ./prod-values.yaml
    asserts:
      - equal:
          path: spec.replicas
          value: 5
```

### Running Tests

```bash
# Run all tests
helm unittest mychart/

# Run with verbose output
helm unittest -3 mychart/

# Run specific test file
helm unittest -f 'tests/deployment_test.yaml' mychart/

# Update snapshots
helm unittest -u mychart/

# Output JUnit XML
helm unittest -o junit -o results.xml mychart/

# With coverage
helm unittest --with-coverage mychart/
```

## 4. Manifest Validation

### kubeconform

Install:
```bash
# macOS
brew install kubeconform

# Linux
curl -LO https://github.com/yannh/kubeconform/releases/latest/download/kubeconform-linux-amd64.tar.gz
tar xf kubeconform-linux-amd64.tar.gz
sudo mv kubeconform /usr/local/bin/
```

Usage:
```bash
# Validate rendered templates
helm template my-release ./mychart | kubeconform -strict -summary

# Validate with specific Kubernetes version
helm template my-release ./mychart | \
  kubeconform -kubernetes-version 1.28.0 -strict -summary

# Validate with CRDs
helm template my-release ./mychart | \
  kubeconform -schema-location default \
  -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
  -strict -summary

# Exit on first error
helm template my-release ./mychart | kubeconform -strict -exit-on-error

# Output JSON
helm template my-release ./mychart | kubeconform -output json
```

### kubeval (deprecated but still used)

```bash
# Install
brew install kubeval

# Validate
helm template my-release ./mychart | kubeval --strict

# Specific Kubernetes version
helm template my-release ./mychart | kubeval --kubernetes-version 1.28.0

# Ignore missing schemas
helm template my-release ./mychart | kubeval --ignore-missing-schemas
```

### Polaris

Policy validation:
```bash
# Install
kubectl apply -f https://github.com/FairwindsOps/polaris/releases/latest/download/dashboard.yaml

# CLI
brew install fairwinds/tap/polaris

# Audit chart
helm template my-release ./mychart | polaris audit --format=pretty

# CI mode
helm template my-release ./mychart | polaris audit --audit-path - --format json
```

## 5. Dry Run Testing

### Basic Dry Run

```bash
# Client-side only (no server validation)
helm install --debug --dry-run my-release ./mychart

# With custom values
helm install --debug --dry-run my-release ./mychart -f custom-values.yaml

# Server-side validation (requires cluster access)
helm template my-release ./mychart | kubectl apply --dry-run=server -f -

# Check resource quotas and limits
helm template my-release ./mychart | kubectl apply --dry-run=server -f - -o yaml
```

### Template Generation

```bash
# Generate all templates
helm template my-release ./mychart

# Generate specific template
helm template my-release ./mychart -s templates/deployment.yaml

# With values
helm template my-release ./mychart --set replicaCount=3

# Show only resource names
helm template my-release ./mychart | grep '^# Source:'

# Output to directory
helm template my-release ./mychart --output-dir ./output
```

### Diff Testing

```bash
# Install helm-diff plugin
helm plugin install https://github.com/databus23/helm-diff

# Show diff before upgrade
helm diff upgrade my-release ./mychart

# Diff with values
helm diff upgrade my-release ./mychart -f new-values.yaml

# Three-way diff
helm diff upgrade my-release ./mychart --three-way-merge
```

## 6. Integration Testing

### Test Pod Template

`templates/tests/test-connection.yaml`:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: "{{ include "mychart.fullname" . }}-test-connection"
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": test
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  containers:
    - name: wget
      image: busybox
      command: ['wget']
      args: ['{{ include "mychart.fullname" . }}:{{ .Values.service.port }}']
  restartPolicy: Never
```

Advanced test:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: "{{ include "mychart.fullname" . }}-test-api"
  annotations:
    "helm.sh/hook": test
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  containers:
    - name: curl
      image: curlimages/curl:latest
      command:
        - /bin/sh
        - -c
        - |
          set -ex
          # Test health endpoint
          curl -f http://{{ include "mychart.fullname" . }}:{{ .Values.service.port }}/health

          # Test API endpoint
          response=$(curl -s http://{{ include "mychart.fullname" . }}:{{ .Values.service.port }}/api/version)
          echo "Response: $response"

          # Test authentication (if applicable)
          {{- if .Values.auth.enabled }}
          curl -f -H "Authorization: Bearer test" \
            http://{{ include "mychart.fullname" . }}:{{ .Values.service.port }}/api/protected
          {{- end }}
  restartPolicy: Never
```

Run tests:
```bash
# Install and run tests
helm install my-release ./mychart
helm test my-release

# Show logs
helm test my-release --logs

# Cleanup after test
helm test my-release --logs && helm uninstall my-release
```

### ct (Chart Testing) Integration Tests

```bash
# Install and test charts in kind cluster
kind create cluster --name chart-testing

# Run tests
ct install --config ct.yaml --chart-dirs charts --helm-extra-args "--timeout 10m"

# Cleanup
kind delete cluster --name chart-testing
```

## 7. CI/CD Pipelines

### GitHub Actions

`.github/workflows/lint-test.yaml`:
```yaml
name: Lint and Test Charts

on:
  pull_request:
    paths:
      - 'charts/**'

jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Set up Helm
        uses: azure/setup-helm@v3
        with:
          version: v3.12.0

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Set up chart-testing
        uses: helm/chart-testing-action@v2.4.0

      - name: Run chart-testing (list-changed)
        id: list-changed
        run: |
          changed=$(ct list-changed --config ct.yaml)
          if [[ -n "$changed" ]]; then
            echo "changed=true" >> $GITHUB_OUTPUT
          fi

      - name: Run chart-testing (lint)
        run: ct lint --config ct.yaml

      - name: Install kubeconform
        run: |
          curl -LO https://github.com/yannh/kubeconform/releases/latest/download/kubeconform-linux-amd64.tar.gz
          tar xf kubeconform-linux-amd64.tar.gz
          sudo mv kubeconform /usr/local/bin/

      - name: Validate manifests
        run: |
          for chart in charts/*; do
            helm template test $chart | kubeconform -strict -summary
          done

      - name: Create kind cluster
        uses: helm/kind-action@v1.5.0
        if: steps.list-changed.outputs.changed == 'true'

      - name: Run chart-testing (install)
        run: ct install --config ct.yaml
        if: steps.list-changed.outputs.changed == 'true'

      - name: Run helm-unittest
        run: |
          helm plugin install https://github.com/helm-unittest/helm-unittest
          for chart in charts/*; do
            helm unittest $chart
          done
```

### GitLab CI

`.gitlab-ci.yml`:
```yaml
stages:
  - lint
  - test
  - validate

variables:
  HELM_VERSION: "3.12.0"

lint:
  stage: lint
  image: alpine/helm:${HELM_VERSION}
  script:
    - apk add --no-cache python3 py3-pip yamllint yamale
    - pip3 install chart-testing
    - ct lint --config ct.yaml
  only:
    changes:
      - charts/**/*

unittest:
  stage: test
  image: alpine/helm:${HELM_VERSION}
  script:
    - helm plugin install https://github.com/helm-unittest/helm-unittest
    - |
      for chart in charts/*; do
        helm unittest $chart
      done
  only:
    changes:
      - charts/**/*

validate:
  stage: validate
  image: alpine/helm:${HELM_VERSION}
  script:
    - apk add --no-cache curl
    - |
      curl -LO https://github.com/yannh/kubeconform/releases/latest/download/kubeconform-linux-amd64.tar.gz
      tar xf kubeconform-linux-amd64.tar.gz
      mv kubeconform /usr/local/bin/
    - |
      for chart in charts/*; do
        helm template test $chart | kubeconform -strict -summary
      done
  only:
    changes:
      - charts/**/*
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    environment {
        HELM_VERSION = '3.12.0'
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
                    helm version
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    for chart in charts/*; do
                        helm lint $chart --strict
                    done
                '''
            }
        }

        stage('Unit Test') {
            steps {
                sh '''
                    helm plugin install https://github.com/helm-unittest/helm-unittest
                    for chart in charts/*; do
                        helm unittest $chart
                    done
                '''
            }
        }

        stage('Validate') {
            steps {
                sh '''
                    curl -LO https://github.com/yannh/kubeconform/releases/latest/download/kubeconform-linux-amd64.tar.gz
                    tar xf kubeconform-linux-amd64.tar.gz
                    chmod +x kubeconform

                    for chart in charts/*; do
                        helm template test $chart | ./kubeconform -strict -summary
                    done
                '''
            }
        }

        stage('Integration Test') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    # Assuming k8s cluster access is configured
                    for chart in charts/*; do
                        helm install test-${BUILD_NUMBER} $chart --wait --timeout 5m
                        helm test test-${BUILD_NUMBER}
                        helm uninstall test-${BUILD_NUMBER}
                    done
                '''
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
```

## 8. Security Scanning

### Trivy

```bash
# Install
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Scan chart
helm template my-release ./mychart | trivy config -

# Scan with severity
helm template my-release ./mychart | trivy config --severity HIGH,CRITICAL -

# Output format
helm template my-release ./mychart | trivy config --format json -
```

### Checkov

```bash
# Install
pip3 install checkov

# Scan chart
helm template my-release ./mychart > manifests.yaml
checkov -f manifests.yaml

# Specific checks
checkov -f manifests.yaml --check CKV_K8S_8,CKV_K8S_9
```

## 9. Best Practices Checklist

### Pre-Release Checklist

- [ ] Chart passes `helm lint --strict`
- [ ] All unit tests pass (`helm unittest`)
- [ ] Manifests validate (`kubeconform`)
- [ ] Schema validation passes (`values.schema.json`)
- [ ] Security scan passes (Trivy/Checkov)
- [ ] Integration tests pass in test cluster
- [ ] Documentation is complete (README.md)
- [ ] NOTES.txt provides useful post-install information
- [ ] Chart version follows SemVer
- [ ] CHANGELOG is updated
- [ ] Signed and provenance file created (for releases)

### Continuous Testing

```bash
# Quick validation during development
helm lint ./mychart && \
helm template test ./mychart | kubeconform -strict -summary && \
helm unittest ./mychart

# Full validation before commit
./scripts/test-chart.sh
```

Example `test-chart.sh`:
```bash
#!/bin/bash
set -e

CHART_DIR="${1:-.}"

echo "==> Linting chart..."
helm lint "$CHART_DIR" --strict

echo "==> Running unit tests..."
helm unittest "$CHART_DIR"

echo "==> Validating manifests..."
helm template test "$CHART_DIR" | kubeconform -strict -summary

echo "==> Checking security..."
helm template test "$CHART_DIR" | trivy config --severity HIGH,CRITICAL -

echo "✓ All tests passed!"
```

---

**Remember**: Testing is not optional. Set up at least basic linting and unit tests for every chart!
