# Useful third-party resources

Links to third-party resources in the Claude Code / AI-agent ecosystem, kept here so they can be
easily refound if/when needed. Summaries reflect each repo's README as of 2026-06-15.

## Karpathy Skills
<https://github.com/multica-ai/andrej-karpathy-skills>

A single `CLAUDE.md` of coding guidelines for Claude Code, derived from Andrej Karpathy's observations
about LLM programming pitfalls. It encodes four core principles — Think Before Coding, Simplicity
First, Surgical Changes, Goal-Driven Execution — to reduce common AI coding mistakes (false
assumptions, overengineering, unintended edits, unclear success criteria). Shipped as both a Claude
Code plugin and a per-project markdown file, with companion Cursor support. *(This is the source our
own [`rules/coding-principles.md`](rules/coding-principles.md) was adapted from.)*

## Open Brain (OB1)
<https://github.com/NateBJones-Projects/OB1>

An open-source, self-hosted infrastructure system that acts as a **persistent memory layer for AI
agents** — one unified database, one AI gateway, and one chat channel that lets multiple AI platforms
(Claude, ChatGPT, Cursor, …) share knowledge without SaaS middleware. Its modular architecture lets
users build extensions (household management, meal planning, networking, job tracking), and it ships
community "recipes" for importing data, pre-built dashboards, and reusable skill packs.

## Superpowers
<https://github.com/obra/superpowers>

"An agentic skills framework & software development methodology that works" — a collection of
**composable skills** that guide coding agents through a full development process, from brainstorming
and design through test-driven implementation and code review. Skills activate automatically based on
development context rather than manual invocation, and it supports multiple agent platforms (Claude
Code, Cursor, GitHub Copilot CLI, and others).

## Everything Claude Code (ECC)
<https://github.com/affaan-m/ECC>

A comprehensive "agent harness operating system" providing skills, instincts, memory, security, and
research-first development across multiple agent platforms (Claude Code, Cursor, OpenCode, Codex, …).
The repo bundles 64 specialized agents, 262 reusable skills, 84 legacy command shims, and
production-ready configs evolved through months of daily use. It works as both a Claude Code plugin and
a manual toolkit, with cross-platform support (Windows/macOS/Linux), memory persistence, continuous
learning, and security scanning (AgentShield).

## Ruflo — multi-agent AI harness
<https://github.com/ruvnet/ruflo>

A multi-agent AI **orchestration framework** that extends Claude Code with coordinated swarm
intelligence, adaptive memory, and autonomous workflows — deploying 100+ specialized agents that
collaborate across machines and trust boundaries. Features include self-learning patterns,
vector-based memory (AgentDB), federation for secure inter-agent communication, multi-LLM-provider
integration, a multi-model chat web UI, a Goal-Oriented Action Planning interface, and a marketplace of
33+ plugins (intelligence, security, testing, DevOps).

## Open Design
<https://github.com/nexu-io/open-design>

An open-source, local-first alternative to Claude Design that generates **design artifacts** directly
through coding agents. A native desktop app (macOS/Windows) with 100+ skills, 150 design systems, and
261 plugins that integrate with Claude Code, Cursor, and GitHub Copilot, producing prototypes,
dashboards, presentations, images, and videos exported as real HTML/CSS/PDF/PPTX/MP4. It keeps
processing local (optional self-hosting), enforces brand consistency via reusable `DESIGN.md` specs,
and operates as a "filesystem of skills, design systems, and plugins" any compatible agent can consume.
