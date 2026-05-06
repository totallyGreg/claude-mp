Show risks by threat actor access level.

```bash
uv run ${CLAUDE_PLUGIN_ROOT}/skills/ai-risk-mapper/scripts/cli_actor_access.py $ARGUMENTS
```

Arguments:
- `<access-level>` - One of: external, api, user, privileged, agent, supply-chain, infrastructure-provider, service-provider, physical
- `--list` - List all access levels with risk counts
- `--offline` - Use bundled schemas

Examples:
```
/arm-actor-access --list
/arm-actor-access agent
/arm-actor-access supply-chain --offline
```
