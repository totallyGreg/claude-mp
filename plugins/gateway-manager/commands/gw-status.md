Check the status of all gateway-related resources in the kgateway-system namespace.

Run the following command to show Gateway, AgentgatewayBackend, and HTTPRoute resources:

```bash
kubectl get gateway,agentgatewaybackend,httproute -n kgateway-system
```

Also check for any AgentgatewayPolicy resources:

```bash
kubectl get agentgatewaypolicy -n kgateway-system
```

Report the results in a readable format, highlighting:
- Gateway status and listeners
- Backend configurations and their providers
- HTTPRoute attachments and path prefixes
- Any resources showing errors or pending status
