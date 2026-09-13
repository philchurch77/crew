---
type: tool_order
before: { tool: Agent, input_match: '"subagent_type"\s*:\s*"(?:[\w-]+:)?gunner"' }
after: { tool: Agent, input_match: '"subagent_type"\s*:\s*"(?:[\w-]+:)?lookout"' }
---
