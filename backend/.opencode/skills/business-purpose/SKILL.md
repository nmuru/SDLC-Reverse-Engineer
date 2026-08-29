---
name: business-purpose
description: Reconstruct the actual business purpose of a software repository from repository evidence. Use when determining what problem the system solves, who it serves, what outcomes it provides, and what the software is fundamentally intended to accomplish.
---

# Business Purpose Reverse-Engineering Skill

## Objective

Determine the most defensible explanation of why the software exists and what real-world problem it is intended to solve.

The output is not a generic description of the repository, a list of technologies, or a restatement of the README. Reconstruct the business purpose from the combined evidence of user-facing behavior, application flows, domain concepts, data structures, APIs, configuration, documentation, tests, and implementation.

The result should explain the software in business terms while remaining grounded in technical evidence.

## When to use

Use this skill for the Business Purpose phase of the nine-phase reverse-engineering workflow.

The repository may be a production system, prototype, internal tool, open-source application, library, service, monorepo, or incomplete implementation. Adapt the investigation to what actually exists.

## Required questions

Determine, as far as the repository allows:

1. What real-world problem does the software appear to solve?
2. Who are the apparent users, operators, customers, or consuming systems?
3. What activity or workflow does the software enable, automate, support, or simplify?
4. What meaningful outcome does a user or consuming system obtain from it?
5. What are the core domain concepts or entities that reveal the problem being addressed?
6. What are the strongest technical signals supporting the inferred purpose?
7. Is the business purpose explicitly documented, strongly implied by implementation, or only partially inferable?
8. What important aspects of the purpose remain unknown?

Do not force answers to questions for which the repository has insufficient evidence.

## Investigation workflow

### Step 1: Establish repository context

Start with repository reconnaissance.

Identify the application entry points, major applications or packages, README and documentation, dependency manifests, configuration, routes, APIs, domain models, schemas, database definitions, UI pages, command-line interfaces, background jobs, integrations, and tests.

Determine whether the repository contains one system or multiple related systems.

Do not begin with the assumption that the repository's name accurately describes its business purpose.

### Step 2: Find explicit purpose statements

Inspect the strongest available sources of explicit intent:

- README files
- project documentation
- product descriptions
- package metadata
- application titles and descriptions
- route or API documentation
- UI labels and navigation
- configuration descriptions
- comments describing domain behavior

Treat these as evidence of stated intent, not automatically as proof of implemented behavior.

Record important discrepancies between stated purpose and implemented behavior.

### Step 3: Identify user-facing behavior

Trace the main externally visible capabilities.

For web applications, inspect routes, pages, forms, API endpoints, request and response schemas, and the backend handlers behind them.

For services or libraries, inspect public APIs, commands, event consumers, and primary entry points.

Ask what a user or consuming system can actually do with the software.

Do not infer business purpose from isolated utility functions when the repository exposes a larger workflow.

### Step 4: Identify domain concepts

Look for domain-specific nouns and relationships in:

- database models
- schemas
- type definitions
- API contracts
- validation rules
- service names
- UI labels
- event names
- configuration
- test fixtures

Determine what these concepts represent in the real-world workflow.

A domain model is particularly valuable when documentation is weak because recurring entities and relationships often reveal what the system is actually managing.

### Step 5: Trace a representative end-to-end workflow

Identify at least one important workflow that demonstrates the system's purpose.

Trace it from an external entry point through the relevant application layers to its outcome.

For example:

user action → API/UI entry point → business/service logic → data or external integration → resulting output.

Do not invent a workflow if the repository does not expose enough evidence to trace one.

The workflow should explain why the major components exist, not merely how they call each other.

### Step 6: Cross-check implementation against intent

Compare explicit documentation with implementation evidence.

Look for:

- documented features that have no implementation
- implemented capabilities absent from documentation
- placeholder or prototype behavior
- deprecated or apparently unused functionality
- multiple competing workflows
- configuration-dependent behavior
- integrations that are declared but not actually used

When these discrepancies materially affect the business-purpose interpretation, state them explicitly.

### Step 7: Form the business-purpose hypothesis

Synthesize the evidence into a concise business-purpose hypothesis.

The hypothesis should identify:

- the problem
- the apparent users or consumers
- the principal workflow
- the resulting business or operational outcome

Use calibrated language such as "the repository indicates," "the implementation strongly suggests," or "the available evidence does not establish" when appropriate.

Do not use vague phrases such as "this is a platform for..." unless the repository provides enough evidence to explain what the platform actually does.

## Evidence requirements

A strong business-purpose conclusion should be supported by multiple evidence types where available.

Prefer combinations such as:

- documentation + user-facing workflow
- API routes + service logic
- domain models + UI behavior
- tests + implementation
- configuration + integration code

Do not treat a project name, README tagline, or directory name as sufficient evidence by itself.

For each major conclusion, identify the relevant repository artifacts in the final analysis.

## Anti-patterns and rationalizations

| Rationalization | Required response |
|---|---|
| "The README already tells us what it does." | Verify the stated purpose against actual entry points and implementation. |
| "The repository name is obvious." | Treat the name only as a clue. Find implementation evidence. |
| "The technology stack tells us the product." | Technology describes implementation, not business purpose. Inspect behavior and domain concepts. |
| "There are many API endpoints, so the purpose is clear." | Trace representative endpoints and determine what real-world workflow they support. |
| "The UI labels are enough." | Cross-check the UI with backend behavior and data models. |
| "The model names clearly reveal the business." | Use them as evidence, but verify their relationships and actual usage. |
| "We can infer the missing parts because this is a common application type." | Do not substitute industry stereotypes for repository evidence. |
| "The code is incomplete, so we should fill in the intended purpose." | Describe what can be established and explicitly identify what remains unknown. |

## Red flags

Stop and investigate further when:

- the README and implementation describe different systems
- multiple unrelated applications exist in one repository
- the apparent core domain models are unused
- major routes lead only to placeholder responses
- configuration suggests optional or alternative implementations
- dependencies imply capabilities that cannot be traced to runtime usage
- documentation uses product language that the code does not support
- the repository appears to be a framework, library, template, or developer tool rather than an end-user application
- the business purpose can only be stated using generic technology terminology

## Verification gate

Before completing this phase, verify all of the following:

- The proposed business purpose is supported by concrete repository evidence.
- At least one representative workflow has been traced where the repository permits it.
- Apparent users or consumers are supported by evidence rather than guessed.
- Core domain concepts have been considered.
- Documentation has been checked against implementation.
- Important contradictions or implementation gaps are disclosed.
- Facts, inferences, and unknowns are distinguishable.
- The conclusion explains the real-world problem and outcome rather than merely describing the software's technical structure.

If these conditions cannot be satisfied because the repository is incomplete, state the limitation explicitly.

## Output expectations

Return a professional dossier-quality Business Purpose analysis.

The result should synthesize the evidence into a coherent explanation rather than reproduce the investigation process.

Include the strongest supporting evidence and distinguish verified facts from inference.

Do not discuss technologies in depth unless they materially help establish business purpose. Detailed technology analysis belongs to later phases.

Do not propose improvements, redesigns, or future features in this phase. Those belong to the Future Directions phase.

The final conclusion should answer, as precisely as the evidence permits:

"What does this software exist to accomplish, for whom, and through what fundamental workflow or outcome?"
