# .agent-team Directory

This directory contains links to upper layer repositories.

## Structure

```
.agent-team/
├── search-r -> ../../SEARCH-R              # Link to L0 (SEARCH-R)
├── research -> ../../agent-team-research   # Link to L1 (agent-team-research)
└── README.md                               # This file
```

## Purpose

Since Git submodules with local file paths have security restrictions,
we use symbolic links to establish dependencies.

## Usage

### Access L0 (SEARCH-R) Resources

```bash
# View methodology
cat .agent-team/search-r/methodology/SEARCH-R-cycle.md

# Access research instances
ls .agent-team/search-r/research-instances/
```

### Access L1 (agent-team-research) Resources

```bash
# Use Research Agent
cat .agent-team/research/agents/research-agent/AGENTS.md

# Access research skills
ls .agent-team/research/agents/research-agent/skills/

# View research templates
ls .agent-team/research/knowledge-base/templates/
```

### Research Delegation Workflow

```bash
# Create research request
vim collaboration/research-requests/request-001.json

# L1 agent picks up request
# L1 uses .agent-team/search-r for methodology
# L1 stores instance in .agent-team/search-r/research-instances/

# Results delivered to specified output path
```

## Platform Compatibility

### macOS/Linux
Symbolic links work natively.

### Windows
Requires:
- Administrator privileges, or
- Developer Mode enabled

Alternative for Windows:
```cmd
# Use junction instead
mklink /J .agent-team\search-r ..\..\SEARCH-R
mklink /J .agent-team\research ..\..\agent-team-research
```

## Future Migration

When repositories are pushed to GitHub:
```bash
# Remove symbolic links
rm .agent-team/search-r
rm .agent-team/research

# Add proper Git submodules
git submodule add https://github.com/{org}/SEARCH-R.git .agent-team/search-r
git submodule add https://github.com/{org}/agent-team-research.git .agent-team/research
```

## Dependency Verification

Verify links work correctly:
```bash
# Test L0 access
cat .agent-team/search-r/opencode.json

# Test L1 access
cat .agent-team/research/opencode.json
```

## Related

- L0 Repository: SEARCH-R (../../SEARCH-R)
- L1 Repository: agent-team-research (../../agent-team-research)
- Dependencies Documentation: ../collaboration/dependencies/README.md

---

**Created**: 2026-03-08
**Purpose**: L0 and L1 dependencies for L2
