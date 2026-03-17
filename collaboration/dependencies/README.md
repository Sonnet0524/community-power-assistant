# Dependencies Documentation

This directory contains documentation about dependencies on L0 and L1 repositories.

## Dependency Structure

```
L2 (AgentTeam-Template)
    ├── Depends on L1 (agent-team-research)
    │   ├── Research Agent capabilities
    │   ├── Research templates
    │   └── Research instance management
    │
    └── Depends on L0 (SEARCH-R)
        ├── SEARCH-R methodology
        ├── Research frameworks
        └── Theory foundations
```

## L1 Dependency: agent-team-research

### Submodule Integration

**Path**: `.agent-team/research` (to be added)

**Purpose**:
- Access Research Agent for research tasks
- Use research templates and skills
- Delegate research work to L1

**Usage**:
```yaml
# In project configuration
research:
  source: .agent-team/research
  agent: research-agent
  skills:
    - web-search
    - document-analysis
    - code-exploration
    - knowledge-synthesis
```

### Research Delegation Workflow

1. **Create Research Request**
   ```
   collaboration/research-requests/{request-id}.json
   ```

2. **L1 Agent Processes**
   - L1 agent receives request
   - Executes research using SEARCH-R methodology
   - Stores instance in L0 research-instances

3. **Receive Research Results**
   - L1 notifies completion
   - Results available in designated output path

## L0 Dependency: SEARCH-R

### Methodology Reference

**Path**: `../SEARCH-R` (relative path)

**Purpose**:
- Access SEARCH-R methodology
- Understand research depth standards
- Follow research best practices

**Usage**:
```yaml
# Reference methodology
methodology:
  source: ../SEARCH-R/methodology/
  cycle: SEARCH-R-cycle.md
  depth: research-depth.md
  templates: ../SEARCH-R/templates/
```

### Research Instance Storage

When delegating research to L1, instances are stored in L0:
```
../SEARCH-R/research-instances/{project-name}/
```

## Integration Benefits

### 1. Clear Responsibility Boundaries
- L0: Provides methodology and theory
- L1: Provides research capabilities
- L2: Provides project management
- L3: Focuses on business implementation

### 2. Reusable Research Capabilities
- Multiple L3 projects can use same L1 research agent
- Research results shared through L0 instances
- Avoid duplication of research efforts

### 3. Standardized Workflows
- Common methodology (SEARCH-R)
- Standard research depth levels
- Consistent documentation formats

## Configuration Files

### opencode.json
- Defines L2 level and relationships
- Specifies dependencies on L0 and L1
- Configures submodule paths

### PM Agent Configuration
- PM Agent can delegate research tasks
- Uses standard research request format
- Tracks research progress through L1

## Related Documentation

- [Research Delegation Guide](../research-requests/README.md)
- [Submodule Setup Guide](./submodule-setup.md)
- [L0-L1-L2 Integration](./integration-diagram.md)

---

**Maintainer**: Migration Agent  
**Created**: 2026-03-08  
**Version**: 1.0
