---
name: low-level-design
description: Reconstruct the concrete internal design of an existing software repository at class, function, module, schema, state, and interaction level. Use when translating the high-level design into evidence-backed implementation structure without turning the analysis into a line-by-line code walkthrough.
---

# Low-Level Design Reverse-Engineering Skill

## Objective

Reconstruct the concrete internal design that implements the system's high-level design.

This phase moves from logical components to the actual modules, classes, functions, interfaces, schemas, data structures, state transitions, algorithms, and internal interactions that make those components work.

The objective is to explain how the implementation is organized internally, not merely to summarize source files.

The analysis must remain evidence-driven. Every important relationship should be traceable to concrete repository artifacts.

Do not redesign the system. Do not silently "clean up" poor design. Describe the implementation that exists, including duplication, coupling, legacy paths, incomplete abstractions, and unusual structures when they materially affect understanding.

## Relationship to other phases

Business Purpose explains why the system exists.

Features explains what meaningful capabilities it provides.

Requirements reconstructs what behaviors and constraints the system appears to satisfy.

Technology Architecture explains the major runtime technologies and boundaries.

High-Level Design explains the major logical components and their responsibilities.

Low-Level Design explains how those logical components are concretely implemented.

Implementation Detail later explains implementation mechanics, configuration, build, deployment, and operational execution in greater depth.

This phase should therefore answer:

"What concrete modules, classes, functions, data structures, interfaces, and interactions implement the high-level design?"

## Scope

Cover the implementation dimensions that materially explain the system:

- module/package organization
- classes and important objects
- functions and methods
- interfaces and abstractions
- schemas and data structures
- validation
- domain logic
- service logic
- persistence access
- external integration adapters
- state management
- important algorithms
- control flow
- dependency relationships
- error propagation
- serialization/deserialization
- configuration-dependent implementation
- significant concurrency or asynchronous mechanisms

Do not attempt to describe every function. Focus on implementation elements that are architecturally or behaviorally significant.

## Investigation workflow

### Step 1: Start from high-level components

Use the High-Level Design results to identify the logical components that require concrete implementation mapping.

For each major component, locate:

- primary modules
- entry classes/functions
- public interfaces
- service objects
- repositories or persistence adapters
- domain objects
- external clients
- validators
- serializers
- configuration dependencies

Do not blindly search the entire repository without a component-level hypothesis.

### Step 2: Map logical components to source artifacts

Create an evidence-backed mapping:

logical component → package/module → classes/functions → important collaborators.

Use:

- imports
- call sites
- type references
- inheritance
- composition
- dependency injection
- route registration
- object construction
- interface implementation
- event registration

Do not map components based solely on filenames.

### Step 3: Identify important entry points

For each major workflow, identify the concrete implementation entry point.

Examples:

- HTTP route handler
- UI event handler
- CLI command
- worker entry point
- event consumer
- scheduled task
- library public API

Trace the entry point into the internal implementation far enough to explain the main control flow.

### Step 4: Reconstruct control flow

For important workflows, follow the actual sequence of calls.

Identify:

- validation
- branching
- service invocation
- domain logic
- persistence
- external calls
- transformation
- result construction
- error propagation

Do not produce a raw call graph containing every helper function.

Focus on the calls that explain meaningful behavior or component boundaries.

### Step 5: Analyze classes and objects

For important classes or objects, determine:

- responsibility
- public methods
- important internal state
- collaborators
- construction/lifecycle
- inheritance or composition
- invariants
- side effects

Only include classes that materially contribute to the system's design.

Do not describe trivial data classes individually unless they represent important domain or interface concepts.

### Step 6: Analyze functions and methods

For important functions and methods, determine:

- purpose
- inputs
- outputs
- important validation
- side effects
- dependencies
- error behavior
- state changes
- external interactions

Use signatures, implementations, call sites, and tests together.

Do not infer a function's behavior from its name alone.

### Step 7: Analyze interfaces and contracts

Inspect:

- Python/TypeScript interfaces
- abstract classes
- protocols
- request/response schemas
- DTOs
- domain types
- event payloads
- serialized structures
- configuration contracts

Determine what each important boundary expects and produces.

Identify where static types and runtime validation differ.

Do not assume an interface is meaningful merely because it exists. Determine whether it has implementations and consumers.

### Step 8: Analyze data structures and schemas

For important data structures, reconstruct:

- fields
- types
- required/optional status
- defaults
- validation
- relationships
- transformations
- lifecycle
- serialization

Trace important data structures through their consumers.

Distinguish transport schemas from domain models and persistence models when the repository does so.

### Step 9: Analyze persistence implementation

Where persistence exists, trace:

model/schema → repository/access layer → database/storage operation → consumer.

Identify:

- queries
- repositories
- ORM usage
- transactions
- migrations
- serialization
- caching
- connection boundaries

Do not duplicate the full database architecture from the Technology Architecture phase. Focus here on the concrete implementation structure.

### Step 10: Analyze external integrations

For important external services, trace:

application component → client/adapter → request construction → external call → response handling → error handling.

Identify provider-specific abstractions and whether the design isolates or couples the application to the provider.

Do not claim an integration is active solely because an SDK is installed.

### Step 11: Analyze state transitions

For important stateful behavior, identify:

- state representation
- initial state
- valid transitions
- transition triggers
- validation
- persistence
- consumers of the resulting state

State may exist in objects, databases, caches, files, UI stores, job records, or external systems.

Do not invent state machines where the repository only contains loosely related status values.

### Step 12: Analyze important algorithms

Identify algorithms or processing logic that materially determines system behavior.

Explain:

- inputs
- major processing stages
- decisions
- transformations
- outputs
- complexity considerations where evidence permits

Do not reproduce large blocks of source code.

Explain the algorithm in precise prose or concise pseudocode when necessary.

### Step 13: Analyze error and exception flow

Trace important errors through the implementation.

Identify:

- validation failures
- domain errors
- integration failures
- persistence errors
- retries
- exception translation
- fallback behavior
- API response conversion
- worker/job failure handling

Focus on errors that materially affect control flow or external behavior.

### Step 14: Analyze configuration-dependent implementation

Identify implementation behavior controlled by:

- environment variables
- configuration files
- feature flags
- provider settings
- runtime modes
- optional dependencies

Determine how configuration changes actual code paths.

Do not describe configuration values without explaining their implementation effect.

### Step 15: Identify dead, legacy, or incomplete implementation

Look for:

- unused functions
- unreachable modules
- deprecated classes
- placeholder implementations
- commented-out logic
- duplicate implementations
- abandoned abstractions
- unused dependencies
- alternate execution paths

Do not label something dead solely because it is not obvious. Use lack of references, configuration, consumers, or execution paths as evidence.

## Low-Level Design Artifacts

Where useful, produce one or more precise diagrams.

Possible diagrams include:

- class relationship diagram
- module dependency diagram
- sequence diagram for a representative workflow
- data transformation diagram
- state transition diagram

Prefer Mermaid when the response format supports it.

Do not create diagrams merely for decoration.

A diagram should be limited to the most important implementation relationships and should remain readable.

For a sequence diagram, show actual participants and meaningful calls.

For a class diagram, include only important classes, attributes, methods, inheritance, and composition relationships.

For a module diagram, show actual dependency direction.

Do not fabricate relationships to make the diagram symmetrical or complete.

## Evidence requirements

For each major low-level design claim, identify concrete artifacts such as:

- file path
- module
- class
- function/method
- type/interface
- schema
- route
- call site
- test
- configuration key

Prefer evidence from implementation and call sites rather than names or comments alone.

When saying "A calls B", establish the call relationship from source.

When saying "A implements interface B", establish the inheritance, protocol, registration, or equivalent mechanism.

When saying "A owns state B", identify where B is created, changed, and consumed.

## Certainty classification

Use:

**Verified:** Directly established by source relationships or multiple strong artifacts.

**Strongly inferred:** Supported by connected implementation evidence but not explicit in one place.

**Unverified:** Suggested by names, documentation, or intended abstractions without enough implementation evidence.

**Apparently unused/legacy:** Present but lacking a credible active path.

Do not convert inferred implementation behavior into verified fact without evidence.

## Distinguishing design from incidental code

Include an implementation element when it materially explains:

- a feature
- a requirement
- a component boundary
- data flow
- state
- integration
- algorithm
- error behavior
- configuration-dependent behavior

Usually exclude:

- trivial getters/setters
- boilerplate
- generated code
- framework internals
- dependency source
- repetitive wrappers with no meaningful behavior

Mention them only when they have architectural or behavioral significance.

## Anti-patterns and rationalizations

| Rationalization | Required response |
|---|---|
| "Low-level design means documenting every function." | Focus on functions and classes that materially explain behavior and structure. |
| "The class name tells us its responsibility." | Verify behavior, collaborators, and call sites. |
| "A method exists, so it is part of the active flow." | Establish reachability and usage. |
| "The interface defines the architecture." | Check implementations and consumers. |
| "Every schema is a domain model." | Distinguish transport, domain, persistence, and configuration structures. |
| "The ORM model proves the database behavior." | Trace actual access code and operations. |
| "An SDK import proves the integration." | Verify actual client creation and calls. |
| "A status enum is a state machine." | Establish actual transitions and transition logic. |
| "The code is messy, so we should describe the cleaner intended design." | Describe the implementation that exists. |
| "We can ignore legacy code." | Include legacy or alternate paths when they affect actual behavior or understanding. |
| "Copying source code is the safest way to be accurate." | Explain behavior and relationships rather than reproducing code. |

## Red Flags

Investigate further when:

- the low-level design is only a list of filenames
- every function has been documented regardless of relevance
- class relationships are inferred from names
- call relationships are claimed without call-site evidence
- interfaces have no identified consumers or implementations
- schemas are described without tracing their use
- important state transitions are missing
- persistence behavior is assumed from model definitions
- external integrations are assumed from dependency declarations
- the diagram contains more elements than can be understood
- implementation detail is being repeated without explaining design significance
- a legacy or duplicate implementation may change which path is actually active

## Verification Gate

Before completing this phase, verify:

- [ ] Major high-level components have been mapped to concrete source artifacts.
- [ ] Important entry points have been identified.
- [ ] Representative workflows have been traced through concrete calls.
- [ ] Important classes and functions have been analyzed at the appropriate level.
- [ ] Important interfaces and contracts have been verified.
- [ ] Significant data structures and schemas have been traced.
- [ ] Persistence implementation has been examined where relevant.
- [ ] External integrations have been traced where relevant.
- [ ] Important state transitions have been examined.
- [ ] Significant algorithms have been identified where relevant.
- [ ] Important error paths have been examined.
- [ ] Configuration-dependent code paths have been considered.
- [ ] Legacy, duplicate, or incomplete paths have been considered.
- [ ] Any low-level diagrams contain evidence-backed relationships.
- [ ] The result is deeper than High-Level Design without becoming a source-code dump.
- [ ] Facts, inferences, and unknowns are distinguishable.

## Output Expectations

Return a professional dossier-quality Low-Level Design analysis.

Organize the result around the major logical components and concrete implementation structures that realize them.

For each significant component, explain the relevant modules, classes, functions, interfaces, data structures, collaborators, state, and important control flows.

Include a precise Mermaid diagram when a class, module, sequence, or state diagram materially improves understanding.

Use source artifacts as evidence and identify important paths precisely.

Do not reproduce large sections of source code.

Do not recommend refactoring or redesign. Describe the existing low-level design, including important weaknesses or irregularities only when they are necessary to understand how the system works.

The final analysis should allow a reader to answer:

"Which concrete modules, classes, functions, contracts, data structures, state transitions, and internal interactions implement the system's high-level design?"
