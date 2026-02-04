# AI Risk Mapper Plugin

Identify, analyze, and mitigate security risks in AI systems using the CoSAI (Coalition for Secure AI) Risk Map framework.

## Installation

Add to your Claude Code plugins or install via the marketplace.

## Commands

Interactive commands for querying the CoSAI risk database:

| Command | Purpose |
|---------|---------|
| `/arm-risk-search <query>` | Search risks by keyword |
| `/arm-control-search <query>` | Search controls by keyword |
| `/arm-controls-for-risk <id>` | Get controls for a specific risk |
| `/arm-persona-profile <id>` | Get risk profile for a persona |
| `/arm-gap-analysis <id>` | Assess control coverage gaps |
| `/arm-framework-map <id>` | Map risk to compliance frameworks |

All commands support `--offline` flag to use bundled schemas.

### Examples

```bash
/arm-risk-search injection
/arm-gap-analysis DP --implemented controlTrainingDataSanitization
/arm-framework-map PIJ --framework mitre-atlas --offline
```

## Skills

### ai-risk-mapper

Triggers on requests like:
- "Analyze security risks in my AI application"
- "Generate a CoSAI risk assessment for this codebase"
- "What AI security risks apply to my RAG pipeline?"

The skill runs automated assessments and generates comprehensive reports aligned with MITRE ATLAS, NIST AI RMF, OWASP Top 10 for LLM, and STRIDE frameworks.

## Resources

- **CoSAI Framework**: https://github.com/cosai-oasis/secure-ai-tooling
- **Bundled schemas**: Offline-capable with cached CoSAI data in `assets/cosai-schemas/`

## Version

4.0.0
