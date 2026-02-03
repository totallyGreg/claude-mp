Tail the controller logs for kgateway and agentgateway to help debug issues.
$ARGUMENTS

If no arguments provided, show the last 50 lines from both controllers.
If a number is provided as argument, use that as the tail count.
If "kgateway" or "agentgateway" is specified, show only those logs.

Commands to use:

For kgateway controller logs:
```bash
kubectl -n kgateway-system logs -l app.kubernetes.io/name=kgateway --tail=50
```

For agentgateway controller logs:
```bash
kubectl -n kgateway-system logs -l app.kubernetes.io/name=agentgateway --tail=50
```

Analyze the logs for:
- Error messages
- Failed reconciliation
- Backend connection issues
- Route attachment problems

Summarize any issues found with recommended fixes.
