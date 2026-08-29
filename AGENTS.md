# ReverseEngineer-SDLC

## Project Purpose

ReverseEngineer-SDLC is a web application whose objective is to produce SDLC documentation for an existing software repository.

The system analyzes an existing repository and reconstructs its business purpose, features, requirements, technology architecture, high-level design, low-level design, implementation details, testing strategy, and future directions.

The repository may have been developed using SDLC, Agile, Scrum, Kanban, Waterfall, or another methodology. The objective of this application is nevertheless to reconstruct documentation corresponding to the defined SDLC phases.

The objective is not generic code summarization. Conclusions should be grounded in concrete repository evidence, with a clear distinction between verified facts, reasonable inferences, and unknowns.

## Mandatory Output Contract

Every phase must produce its final result as a single valid JSON object with exactly two fields:

{
  "phase": "<canonical SDLC phase identifier>",
  "documentation": "<complete final SDLC documentation in Markdown>"
}

The `phase` value must identify the SDLC phase being executed.

The canonical phase identifiers are:

- `business-purpose`
- `features`
- `requirements`
- `technology-architecture`
- `high-level-design`
- `low-level-design`
- `implementation-detail`
- `testing-harness`
- `future-directions`

The `phase` value must correspond to the requested phase.

The `documentation` field contains the actual final SDLC documentation. It is Markdown and will be persisted and presented directly to the user.

The JSON object is a transport format only. Do not include any fields other than `phase` and `documentation`.

Do not output anything before or after the JSON object.

Do not wrap the JSON object in Markdown code fences.

Do not expose internal reasoning, hidden deliberation, tool traces, progress messages, or commentary about the agent's operation.

The documentation must read as if it were produced by the development team as part of the software's normal SDLC documentation. It must not refer to the system message, user message, assistant, agent, model, prompt, skill, OpenCode, tool calls, token usage, or the reverse-engineering process.

This output contract applies to every SDLC phase and every phase-specific skill.

## Agent Architecture

The backend uses a sequential nine-phase analysis pipeline. Each phase is handled by the `reverse-engineer` OpenCode agent and has a corresponding phase-specific skill under `.opencode/skills/`.

The phases are:

1. Business Purpose
2. Features
3. Requirements
4. Technology Architecture
5. High-Level Design
6. Low-Level Design
7. Implementation Detail
8. Testing Harness
9. Future Directions

The target repository is supplied to OpenCode as a Git repository reference. The application creates a lightweight temporary workspace containing the OpenCode configuration, agent instructions, skills, and phase handoff files. OpenCode manages the target repository in its own repository cache and makes it available to the agent for analysis.

Later phases may use outputs from earlier phases, but those handoffs must remain concise and structured. Do not assume that the complete textual output of every previous phase should be inserted into the command line or prompt.

## Evidence and Reasoning

Always inspect the repository directly and ground conclusions in evidence.

Prefer concrete artifacts such as source files, directory structure, package manifests, configuration, APIs, routes, schemas, database definitions, tests, deployment files, and documentation.

Clearly distinguish:

* Facts directly supported by repository evidence.
* Reasonable inferences derived from that evidence.
* Unknowns where the repository does not provide sufficient evidence.

Do not invent implementation details, business capabilities, integrations, requirements, or architecture merely to make the dossier appear complete.

Maintain consistency with conclusions established by earlier phases unless new repository evidence demonstrates that they were incorrect.

## Read-Only Analysis

The analysis is strictly read-only.

Do not modify the target repository.

Do not create, delete, or rewrite files in the target repository.

Do not commit changes.

Do not perform destructive operations.

The agent may inspect files, directories, configuration, dependencies, tests, and other repository artifacts required to perform the analysis.

## Skills

Before performing a phase, load and follow the corresponding phase-specific skill under `.opencode/skills/`.

The skill provides the detailed methodology and expected output for that phase.

Phase-specific skills take precedence over generic assumptions about how that phase should be analyzed, provided they do not conflict with the read-only and evidence-driven requirements above.

## Output

Return the final result for the requested phase using the Mandatory Output Contract.

The `phase` field must identify the requested SDLC phase.

The `documentation` field must contain the complete professional SDLC documentation for that phase in Markdown.

The documentation is the final presentation-ready artifact. There is no required second LLM rendering or rewriting stage.

Do not return internal reasoning, tool traces, progress updates, or unrelated commentary.

Write for a professional software-engineering dossier and assume the reader did not inspect the repository personally.

Be concrete and technically precise. Identify supporting repository artifacts for important findings.

When evidence is incomplete, explicitly state what is unknown and why.

The final nine-phase dossier should read as one coherent reconstruction of the repository, progressing from business purpose through features, requirements, architecture, design, implementation, testing, and future directions.

## Technology Context

The application consists of a Next.js/React/TypeScript frontend and a Python/FastAPI backend.

OpenCode is the coding-agent harness used to execute the analysis agents.

The underlying model/provider is configurable and must not be hard-coded into the conceptual architecture.

Do not assume that Ollama is the only possible model provider.

## Engineering Principles

Keep repository acquisition separate from repository reasoning.

Keep the LLM/model provider separate from agent logic.

Keep phase-specific methodology in the corresponding skills.

Prefer structured and concise handoffs between phases.

Each phase should investigate the repository directly and produce the evidence-backed documentation appropriate to its phase.

The final output should be both analytically rigorous and directly usable as professional SDLC documentation.