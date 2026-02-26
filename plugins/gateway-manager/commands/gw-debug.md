Run a full diagnostic of the gateway system including status, policies, and recent events.

Execute the following diagnostic sequence:

1. Gateway and Backend Status:
```bash
kubectl get gateway,agentgatewaybackend,httproute,agentgatewaypolicy -n kgateway-system -o wide
```

2. Gateway Details:
```bash
kubectl describe gateway ai-gateway -n kgateway-system 2>/dev/null || echo "No ai-gateway found"
```

3. Recent Events:
```bash
kubectl get events -n kgateway-system --sort-by='.lastTimestamp' | tail -20
```

4. Controller Pod Status:
```bash
kubectl get pods -n kgateway-system -l 'app.kubernetes.io/name in (kgateway,agentgateway)'
```

5. Service Status:
```bash
kubectl get svc -n kgateway-system
```

Analyze all outputs and provide:
- Overall system health summary
- Any misconfigurations detected
- Recommended actions to resolve issues
