# External Docs

Checked on 2026-04-02.

## OpenAI
- OpenAI Agents SDK overview: https://openai.github.io/openai-agents-python/
  Notes: emphasizes manager-style orchestration, handoffs, guardrails, tracing, and keeping orchestration logic explicit.
- OpenAI Agents SDK agents guide: https://openai.github.io/openai-agents-python/agents/
  Notes: distinguishes single-agent configuration from multi-agent orchestration and calls out manager-style orchestration versus handoffs.
- OpenAI Agent Builder guide: https://platform.openai.com/docs/guides/agent-builder
  Notes: describes workflows as agents, tools, and control-flow logic assembled into reusable steps.
- OpenAI Agent evals guide: https://platform.openai.com/docs/guides/agent-evals
  Notes: supports validating agent behavior consistently rather than trusting a single narrative output.

## GitHub
- About GitHub Copilot cloud agent: https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent
  Notes: explains that agent work runs independently in its own environment and highlights customization through custom agents, skills, MCP, and hooks.
- About agent skills: https://docs.github.com/en/copilot/concepts/agents/about-agent-skills
  Notes: defines skills as folders of instructions, scripts, and resources that load when relevant.
- Creating agent skills for GitHub Copilot: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-skills
  Notes: confirms `SKILL.md` as the required file and shows that skills are selected based on prompt relevance and description.
- Creating custom agents for Copilot coding agent: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/coding-agent/create-custom-agents
  Notes: supports specialized agents with tailored expertise and explicit selection in the agent UI.

## Practical implication for this skill
- The caller starts the topology.
- The coordinator merges artifacts and should not reinterpret runtime availability after startup.
