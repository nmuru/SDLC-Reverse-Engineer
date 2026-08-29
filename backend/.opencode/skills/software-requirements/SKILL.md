---
name: requirements
description: Reconstruct the functional and non-functional requirements evidenced by an existing software repository. Use when translating implemented behavior, interfaces, constraints, configuration, security, performance, reliability, and operational characteristics into evidence-backed software requirements.
---

# Requirements Reverse-Engineering Skill

## Objective

Reconstruct the requirements that the repository reveals the system was designed to satisfy.

The goal is not to invent a conventional requirements specification from the application's technology stack. The goal is to infer requirements from concrete evidence such as user workflows, APIs, validation rules, domain models, configuration, authentication, persistence, tests, deployment artifacts, error handling, and documented behavior.

Requirements should explain what the system must do, what constraints it operates under, and what qualities or operational conditions it appears to require.

Clearly distinguish requirements that are directly evidenced from those inferred from implementation behavior.

## When to Use

Use this skill for the Requirements phase of the nine-phase reverse-engineering workflow.

This phase follows Business Purpose and Features. Use those results as supporting context, but verify requirements against repository evidence.

Do not turn implementation details into requirements merely because they exist. A requirement should express a behavior, constraint, rule, or quality attribute that the system appears to need to satisfy.

Do not propose missing requirements unless they are explicitly requested as a separate gap analysis. Unknown or unverified requirements should be identified as such.

## Requirement Model

Reconstruct requirements across these categories where evidence exists:

### Functional requirements

What the system must enable or perform.

Examples include:

- accepting a particular input
- creating, updating, retrieving, or deleting domain information
- executing a business workflow
- authenticating a user
- generating a result
- integrating with another system
- processing asynchronous work
- exporting or importing information

### Business and domain rules

Rules governing how the system behaves within the domain.

Examples include:

- validation rules
- eligibility conditions
- state transitions
- required fields
- uniqueness constraints
- calculation rules
- workflow sequencing
- authorization rules
- business-specific invariants

### Interface requirements

Requirements imposed by the system's interfaces.

Consider:

- HTTP APIs
- request and response schemas
- status codes
- CLI interfaces
- file formats
- events
- messages
- public library APIs
- UI interaction requirements

### Data requirements

Requirements concerning information the system must store, retrieve, validate, transform, or preserve.

Consider:

- required entities
- relationships
- identifiers
- persistence
- data validation
- retention behavior
- serialization formats
- transactional behavior
- consistency constraints

Only infer data retention, durability, or consistency requirements when repository evidence supports them.

### Security requirements

Identify evidenced security requirements such as:

- authentication
- authorization
- role or permission boundaries
- credential handling
- secret management
- input validation
- access restrictions
- session behavior
- transport security
- protection of sensitive information

Do not claim that a system is secure merely because it contains a security library or middleware. Describe the actual evidenced controls and the requirement they imply.

### Non-functional requirements

Reconstruct quality attributes that are supported by repository evidence.

Consider:

- performance
- scalability
- availability
- reliability
- concurrency
- observability
- maintainability
- portability
- compatibility
- configurability
- resource constraints

Use stronger language only when the repository provides strong evidence. For example, repeated timeout handling may support a reliability or responsiveness requirement, but it does not automatically establish a numerical performance target.

### Operational and deployment requirements

Where supported, identify requirements associated with:

- environment configuration
- deployment
- startup and shutdown
- health checks
- logging
- monitoring
- background workers
- scheduled jobs
- external services
- secrets
- infrastructure dependencies
- supported runtime versions

These should be expressed as operational requirements rather than as a technology inventory.

## Investigation Workflow

### Step 1: Establish the feature baseline

Review the major capabilities established during the Features phase.

For each meaningful feature, ask:

"What must be true for this feature to work as implemented?"

Use the answer to identify candidate requirements.

Do not simply convert every feature description into a requirement. Decompose each feature into the behaviors, rules, inputs, outputs, and constraints that make it possible.

### Step 2: Extract explicit requirements

Search for explicit requirement evidence in:

- README files
- product documentation
- API documentation
- specifications
- comments
- configuration descriptions
- test descriptions
- acceptance tests
- issue or planning artifacts present in the repository

Treat explicit documentation as evidence of intended requirements. Verify implementation where possible.

### Step 3: Derive functional requirements from behavior

Trace important workflows and identify the conditions and behaviors they depend upon.

For example, if the repository demonstrates a workflow where a user submits an input and receives a generated result, investigate:

- required input
- validation
- accepted formats
- processing behavior
- error conditions
- output contract
- persistence or side effects
- external dependencies

Translate those observations into requirement statements.

Do not include implementation mechanisms unless they express a genuine system constraint.

### Step 4: Extract domain rules

Inspect:

- validation schemas
- conditional logic
- state machines
- database constraints
- authorization checks
- calculations
- defaults
- enumerations
- workflow transitions
- business service logic

Identify rules that constrain valid system behavior.

Distinguish technical validation from domain rules. For example, a string length restriction may be an interface constraint, while a rule requiring a particular business state before an operation may be a domain requirement.

### Step 5: Reconstruct interface requirements

For each significant external interface, inspect the contract.

Determine:

- inputs
- required and optional fields
- accepted values
- validation
- authentication requirements
- output structure
- error behavior
- side effects
- protocol or format constraints

Do not infer requirements from a route name alone. Trace the route to its handler and downstream behavior.

### Step 6: Reconstruct data requirements

Inspect models, schemas, migrations, database definitions, persistence code, serializers, and consumers.

Determine:

- what information must exist
- relationships between entities
- required versus optional information
- uniqueness or integrity constraints
- lifecycle and state
- persistence behavior
- transformations
- external data dependencies

Do not infer durability or retention requirements solely because a database exists.

### Step 7: Reconstruct security requirements

Trace actual authentication and authorization behavior.

Inspect:

- authentication entry points
- authorization checks
- roles and permissions
- session or token handling
- secret/configuration handling
- input validation
- sensitive-data flows
- protected routes

Express what the repository requires and enforces. Do not convert the presence of a security framework into a claim of comprehensive security.

### Step 8: Reconstruct non-functional and operational requirements

Look for evidence in:

- timeout and retry behavior
- concurrency controls
- caching
- queues
- asynchronous processing
- logging
- metrics
- tracing
- health endpoints
- resource limits
- deployment configuration
- environment variables
- runtime constraints
- test performance assumptions
- graceful shutdown behavior

Infer quality requirements conservatively.

For example, retry logic can indicate a requirement for resilience against transient failures. It does not prove a specific availability percentage.

### Step 9: Compare stated and implemented requirements

Identify discrepancies between:

- documentation and implementation
- tests and implementation
- configuration and runtime behavior
- API contracts and actual handlers
- UI assumptions and backend validation
- intended workflows and reachable workflows

Classify material discrepancies rather than silently reconciling them.

### Step 10: Formulate the requirement set

Write requirements in behavior-oriented language.

Prefer:

"The system must reject requests that omit the repository URL."

over:

"`AnalyzeRequest` contains a required `repo_url` field."

The second is evidence supporting the first.

When a requirement is inferred rather than explicitly stated, label or qualify it appropriately.

## Requirement Quality Standard

A strong reconstructed requirement should identify, where applicable:

- actor or triggering condition
- required behavior
- input or precondition
- business or technical constraint
- resulting outcome
- evidence
- certainty level

Avoid requirements that merely restate implementation.

Weak:

"The system must use FastAPI."

Better:

"The system exposes an HTTP interface through which clients can submit repository-analysis requests."

The framework is an architectural implementation detail unless the repository explicitly establishes it as a constraint.

## Evidence and Certainty

Use a practical certainty classification:

**Verified requirement:** Directly stated or strongly established by executable behavior and supporting artifacts.

**Inferred requirement:** Not explicitly stated, but necessary or strongly implied by multiple implementation artifacts.

**Uncertain requirement:** Plausible interpretation with insufficient evidence to establish it confidently.

Do not elevate uncertain requirements to verified requirements.

Where documentation and implementation disagree, report both the stated requirement and the implemented behavior when the distinction matters.

## Anti-patterns and Rationalizations

| Rationalization | Required response |
|---|---|
| "Every feature becomes one requirement." | Decompose features into behaviors, rules, interfaces, and constraints where appropriate. |
| "Every implementation detail is a requirement." | Separate how the system is built from what it must accomplish. |
| "The framework is a requirement because the code uses it." | Treat framework choice as architecture unless repository evidence establishes it as a constraint. |
| "A database means data must be durable forever." | Do not infer retention or durability without evidence. |
| "There is authentication, so the security requirements are complete." | Trace actual controls and identify only evidenced requirements. |
| "Tests prove the complete requirements." | Tests provide strong behavioral evidence but may cover only part of the system. |
| "The README is the requirements specification." | Treat documentation as stated intent and compare it with implementation. |
| "A timeout proves a precise performance target." | Infer resilience or responsiveness only at the level supported by evidence. |
| "A dependency implies a requirement." | Verify actual usage and its role in system behavior. |
| "We should add standard requirements that any system like this should have." | Do not substitute generic best practices for repository evidence. |

## Red Flags

Investigate further when:

- requirements are mostly technology names
- requirements simply duplicate the feature list
- numerical performance targets appear without evidence
- security requirements are inferred solely from security libraries
- data-retention claims are made without persistence or lifecycle evidence
- documentation describes requirements that implementation does not satisfy
- tests cover only a small subset of the claimed behavior
- configuration materially changes behavior but is ignored
- requirements contain words such as "should probably", "normally", or "typically"
- an apparently important requirement has no identifiable implementation evidence

## Verification Gate

Before completing this phase, verify:

- [ ] Major functional requirements have been reconstructed from the feature workflows.
- [ ] Important business/domain rules have been identified.
- [ ] Significant interface contracts and constraints have been examined.
- [ ] Important data requirements have been examined.
- [ ] Evidenced security requirements have been considered.
- [ ] Relevant non-functional requirements have been considered conservatively.
- [ ] Operational and deployment constraints have been considered where supported.
- [ ] Documentation has been compared with implementation.
- [ ] Requirements are distinguished from implementation details.
- [ ] Verified, inferred, and uncertain requirements are distinguishable.
- [ ] Unsupported numerical targets and generic best-practice requirements have been excluded.
- [ ] Important contradictions or gaps are explicitly identified.
- [ ] The result is grounded in repository evidence.

## Output Expectations

Return a professional dossier-quality Requirements analysis.

Organize the result around meaningful functional, domain, interface, data, security, non-functional, and operational requirements as applicable to the repository.

For each important requirement, provide enough context to explain what the system must do or satisfy, why the requirement is supported, and how certain the conclusion is.

Do not turn the output into a code walkthrough. Source symbols and implementation details should be used as evidence rather than becoming the requirement itself.

Do not propose new requirements or redesign the system. If the repository appears to lack an important requirement, identify the absence or uncertainty rather than inventing the missing requirement.

The final analysis should allow a reader to answer:

"What behaviors, rules, interfaces, data constraints, quality attributes, and operational conditions does the repository indicate this system is required to satisfy?"
