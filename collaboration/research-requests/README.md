# Research Requests

This directory contains research requests delegated from L2 to L1.

## Purpose

- Store research requests for L1 research agent
- Track research task status
- Manage research deliverables

## Request Format

### File Naming

```
{request-id}-{short-description}.json
```

Example: `research-20260308-001-architecture-comparison.json`

### Request Structure

```json
{
  "request_id": "research-20260308-001",
  "created_at": "2026-03-08T15:30:00Z",
  "created_by": "pm-agent",
  "project_name": "knowledge-assistant-dev",
  
  "research": {
    "title": "Architecture Comparison",
    "description": "Compare microservices vs monolithic architecture for the project",
    "goals": [
      "Evaluate pros and cons",
      "Assess team capabilities",
      "Provide recommendation"
    ],
    "scope": {
      "depth": "Level 0-2",
      "areas": ["architecture", "team", "scalability"],
      "constraints": ["budget", "timeline", "team size"]
    },
    "methodology": "SEARCH-R"
  },
  
  "deliverables": {
    "format": ["report", "comparison-matrix"],
    "output_path": "reports/research/",
    "deadline": "2026-03-10T18:00:00Z"
  },
  
  "status": {
    "current": "pending",
    "assigned_to": null,
    "l1_instance_id": null,
    "progress": 0,
    "updates": []
  },
  
  "priority": "high",
  "tags": ["architecture", "decision-support"]
}
```

## Workflow

### 1. Create Request

PM Agent creates research request:
```
1. Identify research need
2. Create request file
3. Set status to "pending"
4. Notify L1 research agent
```

### 2. L1 Processing

L1 research agent:
```
1. Pick up pending request
2. Create L0 research instance
3. Execute SEARCH-R cycle
4. Update request status
```

### 3. Result Delivery

When research completes:
```
1. L1 updates status to "completed"
2. Deliverables stored in output_path
3. PM Agent notified
4. Request archived
```

## Status Tracking

### Status Values

- **pending**: Request created, not started
- **assigned**: L1 agent assigned
- **in_progress**: Research in progress
- **review**: Results ready for review
- **completed**: Research completed
- **cancelled**: Request cancelled

### Progress Updates

Each status update includes:
```json
{
  "timestamp": "2026-03-08T16:00:00Z",
  "status": "in_progress",
  "phase": "Explore",
  "progress": 40,
  "notes": "Gathering reference materials"
}
```

## Priority Levels

- **critical**: Blocks project progress
- **high**: Important for next sprint
- **medium**: Valuable but not urgent
- **low**: Nice to have

## Integration with L0

When L1 processes a request:
1. Creates instance in L0: `../SEARCH-R/research-instances/{project}/{instance-id}.json`
2. Follows L0 methodology
3. Uses L0 templates
4. Stores outputs according to L0 standards

## Examples

### Example 1: Technology Evaluation

```json
{
  "request_id": "research-20260308-002",
  "research": {
    "title": "State Management Library Evaluation",
    "description": "Evaluate Redux, MobX, and Zustand for the project",
    "goals": [
      "Compare features and performance",
      "Assess learning curve",
      "Recommend best option"
    ]
  }
}
```

### Example 2: Best Practices Research

```json
{
  "request_id": "research-20260308-003",
  "research": {
    "title": "React Performance Optimization",
    "description": "Research best practices for React performance",
    "goals": [
      "Identify common performance issues",
      "Find optimization strategies",
      "Create implementation checklist"
    ]
  }
}
```

## Related

- [Dependencies Documentation](../dependencies/README.md)
- L1 Repository: agent-team-research
- L0 Repository: SEARCH-R

---

**Maintainer**: Migration Agent  
**Created**: 2026-03-08  
**Version**: 1.0
