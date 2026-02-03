# Gateway-Proxy Standalone Plugin

**Date**: 2026-02-03
**Skill**: gateway-proxy
**Status**: Planning

## Goal

Create gateway-proxy as a **standalone plugin** within the totally-tools marketplace, bundling the skill and its commands as one independently installable unit.

## Architecture

Each plugin in the marketplace is self-contained with its own manifest and components:

```
claude-mp/                                    # Marketplace repository
├── .claude-plugin/
│   └── marketplace.json                      # References all plugins
├── plugins/                                  # Standalone plugins
│   └── gateway-proxy/                        # Self-contained plugin
│       ├── .claude-plugin/
│       │   └── plugin.json                   # Plugin manifest
│       ├── commands/
│       │   ├── gw-status.md
│       │   ├── gw-logs.md
│       │   ├── gw-debug.md
│       │   ├── gw-backend.md
│       │   └── gw-route.md
│       └── skills/
│           └── gateway-proxy/
│               ├── SKILL.md
│               ├── IMPROVEMENT_PLAN.md
│               └── references/
│                   ├── lessons-learned.md
│                   ├── resource-patterns.md
│                   ├── provider-backends.md
│                   └── mcp-routing.md
└── skills/                                   # Legacy location (to be migrated)
    └── gateway-proxy/                        # Current location
```

## Key Architectural Points

| Aspect | Description |
|--------|-------------|
| **Plugin isolation** | Each plugin is independently installable |
| **Auto-discovery** | Commands from `commands/`, skills from `skills/*/SKILL.md` |
| **Bundled distribution** | Skill + commands installed together as one unit |
| **Marketplace reference** | Points to plugin root, not individual components |

## Implementation Tasks

### 1. Create Plugin Directory Structure

```bash
mkdir -p plugins/gateway-proxy/.claude-plugin
mkdir -p plugins/gateway-proxy/commands
mkdir -p plugins/gateway-proxy/skills/gateway-proxy
```

### 2. Create Plugin Manifest

**File**: `plugins/gateway-proxy/.claude-plugin/plugin.json`

```json
{
  "name": "gateway-proxy",
  "version": "1.0.0",
  "description": "Expert guidance for kgateway and agentgateway with kubectl commands for AI/LLM routing, MCP server routing, and API gateway patterns",
  "author": {
    "name": "J. Greg Williams",
    "email": "283704+totallyGreg@users.noreply.github.com"
  },
  "license": "MIT",
  "keywords": ["kubernetes", "gateway", "kgateway", "agentgateway", "llm", "mcp"]
}
```

### 3. Move Existing Skill Content

```bash
# Move skill files to new location
mv skills/gateway-proxy/* plugins/gateway-proxy/skills/gateway-proxy/
rmdir skills/gateway-proxy
```

### 4. Update marketplace.json

Replace current entry (if exists) or add new entry:

```json
{
  "name": "gateway-proxy",
  "description": "Expert guidance for kgateway and agentgateway for AI/LLM routing, MCP server routing, and API gateway patterns",
  "category": "infrastructure",
  "version": "1.0.0",
  "author": {
    "name": "J. Greg Williams",
    "email": "283704+totallyGreg@users.noreply.github.com"
  },
  "source": "./plugins/gateway-proxy",
  "skills": ["./"]
}
```

### 5. Create Commands

All commands in `plugins/gateway-proxy/commands/`:

#### gw-status.md
```markdown
Check the status of all gateway-related resources in the kgateway-system namespace.

Run the following command to show Gateway, AgentgatewayBackend, and HTTPRoute resources:

kubectl get gateway,agentgatewaybackend,httproute -n kgateway-system

Also check for any AgentgatewayPolicy resources:

kubectl get agentgatewaypolicy -n kgateway-system

Report the results in a readable format, highlighting:
- Gateway status and listeners
- Backend configurations and their providers
- HTTPRoute attachments and path prefixes
- Any resources showing errors or pending status
```

#### gw-logs.md
```markdown
Tail the controller logs for kgateway and agentgateway to help debug issues.
$ARGUMENTS

If no arguments provided, show the last 50 lines from both controllers.
If a number is provided as argument, use that as the tail count.
If "kgateway" or "agentgateway" is specified, show only those logs.

Commands to use:

For kgateway controller logs:
kubectl -n kgateway-system logs -l app.kubernetes.io/name=kgateway --tail=50

For agentgateway controller logs:
kubectl -n kgateway-system logs -l app.kubernetes.io/name=agentgateway --tail=50

Analyze the logs for:
- Error messages
- Failed reconciliation
- Backend connection issues
- Route attachment problems

Summarize any issues found with recommended fixes.
```

#### gw-debug.md
```markdown
Run a full diagnostic of the gateway system including status, policies, and recent events.

Execute the following diagnostic sequence:

1. Gateway and Backend Status:
kubectl get gateway,agentgatewaybackend,httproute,agentgatewaypolicy -n kgateway-system -o wide

2. Gateway Details:
kubectl describe gateway ai-gateway -n kgateway-system 2>/dev/null || echo "No ai-gateway found"

3. Recent Events:
kubectl get events -n kgateway-system --sort-by='.lastTimestamp' | tail -20

4. Controller Pod Status:
kubectl get pods -n kgateway-system -l 'app.kubernetes.io/name in (kgateway,agentgateway)'

5. Service Status:
kubectl get svc -n kgateway-system

Analyze all outputs and provide:
- Overall system health summary
- Any misconfigurations detected
- Recommended actions to resolve issues
```

#### gw-backend.md
```markdown
Generate an AgentgatewayBackend YAML template for the specified provider.
$ARGUMENTS

Supported providers: ollama, openai, anthropic, gemini

If no provider specified, list the available providers and their requirements.

Based on the provider argument, generate the appropriate YAML:

For ollama:
- No API key required
- Uses host.internal for OrbStack
- OpenAI-compatible API

For openai, anthropic, gemini:
- Requires Secret with API key
- Include both Secret and AgentgatewayBackend resources

Output the complete YAML that can be applied with kubectl apply -f.

Include comments explaining:
- Required environment variables
- Common model options
- How to test the backend after creation

Reference the gateway-proxy skill for detailed patterns.
```

#### gw-route.md
```markdown
Generate an HTTPRoute YAML template for routing to a backend.
$ARGUMENTS

The argument should be the route name (e.g., "ollama", "openai", "mcp").

Generate an HTTPRoute that:
1. Attaches to the ai-gateway Gateway
2. Matches the path prefix /<name>
3. Includes URLRewrite filter to strip the prefix (for AI backends)
4. References the corresponding AgentgatewayBackend

For AI backends (ollama, openai, anthropic, gemini):
- Include URLRewrite with ReplacePrefixMatch: /

For MCP backends:
- No URL rewriting needed

Output the complete YAML ready for kubectl apply.

Include a test command to verify the route works after creation.

Reference the gateway-proxy skill for detailed patterns.
```

### 6. Update SKILL.md

Add a "Quick Commands" section:

```markdown
## Quick Commands

This plugin includes slash commands for common gateway operations:

| Command | Purpose |
|---------|---------|
| `/gw-status` | Show all gateway resources status |
| `/gw-logs [count\|controller]` | Tail controller logs for debugging |
| `/gw-debug` | Full diagnostic with events and recommendations |
| `/gw-backend <provider>` | Generate backend YAML (ollama, openai, anthropic, gemini) |
| `/gw-route <name>` | Generate HTTPRoute YAML with path rewriting |
```

## Migration Considerations

### Existing Skills in `skills/` Directory

The current marketplace has skills in `skills/` at the root level. Options:

1. **Gradual migration**: New plugins go to `plugins/`, existing skills remain until migrated
2. **Full migration**: Move all skills to standalone plugin format in `plugins/`

**Recommendation**: Start with gateway-proxy as the pattern, then migrate others incrementally.

### Backward Compatibility

Update marketplace.json to support both patterns during transition:
- Legacy: `"source": "./skills/terminal-guru"`
- New: `"source": "./plugins/gateway-proxy"`

## Validation Steps

### Structure Validation
```bash
# Verify plugin structure
ls -la plugins/gateway-proxy/
ls -la plugins/gateway-proxy/.claude-plugin/
ls -la plugins/gateway-proxy/commands/
ls -la plugins/gateway-proxy/skills/gateway-proxy/
```

### Marketplace Validation
```bash
# Validate marketplace
python3 skills/marketplace-manager/scripts/add_to_marketplace.py validate
```

### Skill Validation
```bash
# Validate skill content
uv run skills/skillsmith/scripts/evaluate_skill.py plugins/gateway-proxy/skills/gateway-proxy --quick --strict
```

### Command Testing
Test each command in Claude Code after installation:
- `/gw-status`
- `/gw-logs`
- `/gw-logs 100`
- `/gw-debug`
- `/gw-backend ollama`
- `/gw-backend openai`
- `/gw-route ollama`

## Implementation Sequence

1. Create GitHub Issue for tracking
2. Create plugin directory structure
3. Create plugin.json manifest
4. Move existing skill content
5. Create command files
6. Update SKILL.md with commands section
7. Update marketplace.json
8. Run validation
9. Update IMPROVEMENT_PLAN.md
10. Two-commit release

## Related

- GitHub Issue: TBD (gateway-proxy plugin)
- GitHub Issue: #27 (marketplace-manager architecture documentation)
- Marketplace: totally-tools
