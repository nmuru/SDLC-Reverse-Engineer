---

name: implementation-detail
description: Reconstruct how an existing software repository is concretely configured, built, started, packaged, tested, deployed, operated, and observed. Use when explaining the executable and operational mechanics that turn the implemented system into a running application.
compatibility: opencode
-----------------------

# Implementation Detail Reverse-Engineering Skill

## Objective

Reconstruct the practical implementation mechanics that allow the software repository to become a functioning system.

Explain how the application is configured, assembled, initialized, executed, built, packaged, tested, deployed, operated, and observed.

This phase examines the operational path from repository artifacts to running behavior.

The objective is not to repeat the Low-Level Design analysis of classes, functions, modules, and internal algorithms. Instead, explain how those implementation elements are wired together and made executable in real environments.

Treat the repository as evidence.

Do not describe an intended deployment architecture merely because it appears in documentation. Do not assume that a dependency, configuration file, container definition, workflow, or deployment manifest is active. Establish the actual execution path wherever repository evidence permits.

Do not redesign the system. Describe how the implementation works as it exists, including inconsistencies, alternate paths, obsolete configuration, development-only mechanisms, incomplete deployment infrastructure, and operational weaknesses when they materially affect understanding.

The central question of this phase is:

"How is this software concretely configured, assembled, started, built, packaged, tested, deployed, operated, and observed?"

## Relationship to other phases

Business Purpose explains why the system exists.

Features explain what meaningful capabilities it provides.

Business Requirements and Software Requirements explain the behaviors and constraints the implementation appears intended to satisfy.

Technology Architecture explains the major technologies, platforms, infrastructure boundaries, and runtime dependencies.

High-Level Design explains the major logical components and their responsibilities.

Low-Level Design explains the concrete modules, classes, functions, data structures, contracts, and internal interactions that implement those components.

Implementation Detail explains how those concrete implementation pieces are configured and assembled into an executable system.

Testing Harness explains how behavior is verified.

Design Pattern explains recurring structural or behavioral design techniques.

Future Directions explains evidence-backed possible evolution.

Do not duplicate Low-Level Design merely by listing classes and functions again.

When overlap is unavoidable, use Low-Level Design to identify the implementation structure and use this phase to explain how that structure participates in startup, configuration, execution, packaging, deployment, operation, or observation.

## Scope

Investigate the implementation mechanics that materially explain how the software works in practice.

Cover, where relevant:

* repository entry points
* startup and initialization sequence
* application composition and dependency wiring
* configuration sources and precedence
* environment variables
* secrets references without exposing secret values
* dependency management
* package management
* build process
* compilation or transpilation
* bundling
* code generation
* migrations
* static assets
* runtime process model
* CLI execution
* web server startup
* worker startup
* scheduled processes
* background jobs
* containerization
* image construction
* packaging
* artifact generation
* CI execution
* CD workflows
* deployment manifests
* infrastructure configuration
* runtime modes
* feature flags
* environment-specific behavior
* initialization ordering
* lifecycle hooks
* shutdown behavior
* retry and recovery behavior
* logging
* metrics
* tracing
* health checks
* readiness checks
* operational diagnostics
* test execution mechanics

Do not force every category onto every repository.

Only describe mechanisms supported by evidence.

## Investigation strategy

Approach the repository from the outside in.

Begin with the artifacts that determine how software is invoked and assembled before examining deeper implementation details.

Prioritize evidence that answers:

1. What command or event starts the system?
2. What code receives control first?
3. What configuration is loaded?
4. What dependencies or services are initialized?
5. What processes or runtime components are created?
6. How does the software remain operational?
7. How is it built or packaged?
8. How is it tested?
9. How is it deployed?
10. How can operators observe or diagnose it?

Construct an execution model rather than a directory inventory.

## Investigation workflow

### Step 1: Inventory executable and operational artifacts

Locate repository artifacts that can influence execution.

Inspect, as applicable:

* README files
* AGENTS.md and agent instructions
* package manifests
* lock files
* requirements files
* pyproject files
* setup files
* Makefiles
* Taskfiles
* shell scripts
* npm scripts
* Python entry-point declarations
* Dockerfiles
* compose files
* Kubernetes manifests
* Helm charts
* Terraform or infrastructure definitions
* CI workflow files
* deployment configuration
* environment examples
* configuration files
* service definitions
* process-manager configuration
* test configuration

Do not assume that every discovered artifact belongs to the active execution path.

Classify artifacts as active, alternate, development-only, test-only, generated, legacy, or uncertain where evidence permits.

### Step 2: Identify the primary execution entry point

Determine how the main application starts.

Look for evidence such as:

* executable package declarations
* main functions
* `if __name__ == "__main__"` blocks
* framework launch commands
* CLI definitions
* process scripts
* container commands
* service configuration
* workflow commands
* README instructions that are confirmed by implementation

Trace:

invocation → bootstrap code → configuration loading → application construction → runtime start.

Distinguish between:

* documented entry points
* development entry points
* test entry points
* production entry points
* alternate entry points
* historical or unused entry points

Do not claim a README command is authoritative unless repository configuration or code supports it.

### Step 3: Reconstruct the bootstrap sequence

Trace what happens after control enters the application.

Identify, where applicable:

* argument parsing
* environment detection
* configuration loading
* logging initialization
* dependency construction
* database initialization
* migration checks
* external client initialization
* route registration
* middleware registration
* worker initialization
* cache initialization
* background task registration
* lifecycle hook registration
* server startup

Construct the meaningful order of initialization.

When initialization order affects correctness, explicitly explain the dependency.

For example:

configuration → logging → dependency clients → application assembly → route registration → runtime server

Only show relationships supported by source or runtime configuration.

### Step 4: Analyze application composition and dependency wiring

Determine how concrete implementation objects become a running application.

Inspect:

* constructors
* factories
* application builders
* dependency injection
* service registration
* module imports
* framework configuration
* plugin registration
* singleton initialization
* global application objects
* startup hooks

Answer:

* Where are major dependencies created?
* Where are implementations selected?
* Are dependencies injected or constructed internally?
* Does configuration influence implementation selection?
* Are external clients initialized once or per request?
* Are there multiple composition roots?

Do not confuse ordinary imports with architectural dependency injection.

### Step 5: Reconstruct configuration sources and precedence

Identify every material configuration mechanism.

Possible sources include:

* environment variables
* dotenv files
* YAML
* JSON
* TOML
* framework configuration
* command-line arguments
* secrets managers
* deployment variables
* hard-coded defaults

For each important configuration value, establish:

configuration source → loading mechanism → validation/default → consumer → behavioral effect.

Identify precedence when evidence exists.

For example:

command-line value → environment variable → configuration file → code default

Do not invent precedence from common framework conventions.

Distinguish:

* required configuration
* optional configuration
* secret references
* environment-specific configuration
* deprecated configuration
* unused configuration

Never expose actual credentials, tokens, passwords, private keys, or other sensitive values in the analysis.

### Step 6: Analyze dependency and package management

Determine how runtime and development dependencies are declared and resolved.

Inspect:

* package manifests
* lock files
* requirements files
* dependency groups
* build-system declarations
* workspace definitions
* vendored dependencies
* generated dependency metadata

Explain:

* primary runtime dependencies
* development-only dependencies
* build dependencies
* optional dependencies
* dependency resolution mechanisms
* version pinning strategy when visible
* multiple package ecosystems if present

Do not equate a declared dependency with active runtime usage.

Where important, distinguish:

declared dependency → imported dependency → runtime-instantiated dependency.

### Step 7: Reconstruct build and artifact generation

Determine whether the repository requires transformation before execution.

Inspect:

* build scripts
* compiler configuration
* transpiler configuration
* bundler configuration
* code generators
* asset pipelines
* schema generation
* OpenAPI generation
* protobuf generation
* database migrations
* static-site generation

Trace:

source artifacts → transformation steps → generated artifacts → runtime or deployment artifact.

Identify whether generated files are committed, produced during CI, produced during image construction, or generated locally.

Do not describe a repository as having a build pipeline merely because a generic build script exists. Determine what the script actually does.

### Step 8: Reconstruct the local development workflow

Determine the practical path used to run the system during development.

Trace, where supported:

installation → configuration → dependency setup → prerequisite services → migrations/setup → development command → running process.

Identify:

* development server behavior
* hot reload
* file watching
* mock services
* local databases
* seeded data
* test fixtures
* development-only configuration

Distinguish a reproducible repository workflow from undocumented assumptions about a developer's local environment.

### Step 9: Analyze runtime process topology

Determine what processes exist when the system runs.

Examples include:

* web server
* API process
* frontend server
* worker
* scheduler
* queue consumer
* cron process
* migration process
* sidecar
* background task runner

Construct an evidence-backed process model.

For each important process, identify:

* startup command
* entry point
* responsibility
* dependencies
* communication boundaries
* lifecycle

Do not infer separate processes merely because the code contains asynchronous functions or background classes.

### Step 10: Analyze asynchronous and background execution

Where applicable, determine how work leaves the immediate request or command path.

Inspect:

* queues
* task frameworks
* worker processes
* async runtimes
* thread pools
* process pools
* schedulers
* event consumers
* callbacks
* polling loops

Trace:

trigger → work creation → transport or scheduler → execution context → completion or failure handling.

Distinguish genuine asynchronous execution from synchronous code using asynchronous syntax.

### Step 11: Analyze persistence initialization and migrations

Where persistent storage exists, determine how it becomes operational.

Trace:

configuration → connection construction → schema/migration mechanism → runtime access.

Inspect:

* connection configuration
* initialization hooks
* migration commands
* migration files
* seed mechanisms
* schema generation
* transaction setup

Do not repeat the persistence design already documented in Low-Level Design.

Focus on operational mechanics:

how storage is configured, initialized, evolved, and made available at runtime.

### Step 12: Analyze external service initialization

Determine how external dependencies become usable.

For each material integration, inspect:

* configuration loading
* client construction
* authentication mechanism
* connection lifecycle
* timeout configuration
* retry behavior
* startup validation
* fallback behavior

Trace:

configuration → client initialization → runtime consumer.

Do not expose secrets.

Do not claim connectivity has been verified unless tests, health checks, runtime probes, or explicit repository evidence establish it.

### Step 13: Analyze containerization and packaging

Where containers or distributable packages exist, determine how they are constructed.

Inspect:

* Dockerfiles
* compose files
* image build scripts
* package definitions
* release workflows
* artifact upload steps

Trace:

source repository → build context → dependency installation → generated artifacts → runtime image or package → startup command.

Identify:

* build stages
* runtime stages
* copied artifacts
* environment assumptions
* exposed ports
* volumes
* process command
* development versus production images

Do not assume that a Dockerfile represents the production deployment path if it is only referenced by local development tooling.

### Step 14: Analyze deployment mechanics

Determine how the repository reaches a runtime environment.

Inspect evidence such as:

* CI/CD workflows
* deployment scripts
* infrastructure-as-code
* container registries
* platform manifests
* Kubernetes resources
* Helm charts
* cloud configuration

Trace, where evidence permits:

commit or release → build → artifact/image → deployment action → runtime environment.

Distinguish:

* implemented deployment automation
* manually documented deployment
* partial infrastructure
* environment-specific deployment
* unused deployment artifacts

Do not invent cloud architecture from dependency names or environment variables.

### Step 15: Analyze runtime modes and environment variation

Identify meaningful differences between environments or modes.

Examples:

* development
* test
* staging
* production
* debug
* local
* mock mode
* provider-specific mode

For each important mode, determine:

trigger → configuration difference → implementation effect → operational consequence.

Do not treat a variable named `ENV` or `DEBUG` as proof of meaningful branching without tracing its consumers.

### Step 16: Analyze logging and diagnostics

Determine how the system reports what it is doing.

Inspect:

* logger initialization
* log configuration
* log levels
* structured logging
* exception logging
* correlation identifiers
* request identifiers
* diagnostic endpoints
* debug modes

Trace important operational failures to their observable output where possible.

Distinguish between:

* logging capability
* actual logging use
* production observability

Do not claim structured observability from isolated logging statements.

### Step 17: Analyze metrics, tracing, and health mechanisms

Inspect for:

* metrics libraries
* telemetry initialization
* tracing providers
* spans
* health endpoints
* readiness checks
* liveness checks
* dependency probes

For each mechanism, establish:

instrumentation initialization → instrumented component → exported signal → consumer or endpoint.

Do not claim monitoring exists merely because instrumentation dependencies are declared.

Distinguish:

* implemented instrumentation
* configured export
* deployment-level collection
* actual alerting

### Step 18: Analyze shutdown, recovery, and lifecycle behavior

Determine how the system behaves when stopping or recovering.

Inspect:

* signal handlers
* shutdown hooks
* context managers
* graceful termination
* connection cleanup
* worker draining
* retry mechanisms
* restart policies
* supervisor configuration

Trace important lifecycle paths:

startup → normal operation → failure/retry → shutdown.

Do not infer graceful shutdown from framework capability unless repository code or deployment configuration enables it.

### Step 19: Analyze test execution mechanics

Coordinate with the Testing Harness phase without duplicating its behavioral analysis.

Focus here on how tests are executed.

Inspect:

* test commands
* test runners
* configuration files
* fixtures
* environment setup
* test databases
* mocks
* containers
* CI test steps
* coverage commands

Explain:

command or workflow → environment preparation → test execution → result or coverage artifact.

Leave detailed assessment of test coverage and behavioral verification primarily to the Testing Harness phase.

### Step 20: Identify generated, development-only, legacy, and inactive mechanisms

Actively search for implementation paths that can mislead the analysis.

Look for:

* unused startup scripts
* obsolete Dockerfiles
* duplicate configuration systems
* deprecated commands
* commented deployment paths
* abandoned CI workflows
* stale environment variables
* alternate entry points
* example-only configuration
* placeholder integrations
* generated artifacts mistaken for source
* test-only runtime paths

Classify a mechanism as apparently inactive only when evidence supports that conclusion.

Useful evidence includes:

* no references
* no workflow consumer
* no documented execution path combined with no source references
* superseding implementation
* explicit deprecation
* unreachable configuration

Do not call something dead merely because its purpose is not immediately obvious.

## Evidence model

Support every material implementation-detail claim with repository evidence.

Prefer the following evidence hierarchy:

1. Executable code and actual invocation paths
2. Build, package, container, or workflow configuration
3. Runtime configuration and deployment manifests
4. Tests that exercise startup or execution paths
5. Documentation confirmed by implementation
6. Documentation or comments without confirming evidence

For major claims, identify concrete artifacts such as:

* file path
* command
* script name
* manifest entry
* configuration key
* environment variable name
* workflow job
* container stage
* entry-point function
* startup hook
* test command
* deployment resource

When stating that a command starts a process, establish the command and the receiving entry point.

When stating that configuration affects behavior, identify the configuration definition and its consumer.

When stating that a CI workflow performs a build or deployment, identify the relevant workflow step.

When stating that a service is operationally required, distinguish direct repository evidence from inference.

## Execution-chain reconstruction

For the most important runtime path, reconstruct an explicit chain when possible.

Use a form similar to:

developer or deployment command
→ package/script/task
→ bootstrap entry point
→ configuration loading
→ dependency initialization
→ application assembly
→ runtime process
→ externally observable behavior

For build or release mechanics, use:

source revision
→ dependency resolution
→ transformation/build
→ artifact or image
→ deployment action
→ runtime environment

For background work, use:

trigger
→ scheduling or queueing mechanism
→ worker or execution context
→ result or failure path

Only include arrows representing relationships established by evidence.

## Operational diagrams

Produce a diagram only when it materially improves understanding.

Useful diagrams include:

* startup sequence diagram
* process topology diagram
* build pipeline diagram
* deployment flow diagram
* configuration flow diagram
* lifecycle diagram

Prefer Mermaid when supported.

Keep diagrams focused.

For a startup sequence, show actual components and meaningful initialization calls.

For a process topology diagram, distinguish separate processes from internal modules.

For a deployment diagram, distinguish repository artifacts from infrastructure only when repository evidence establishes the connection.

Do not create a diagram merely because diagrams are expected.

## Certainty classification

Use the following classifications when evidence strength matters.

**Verified:** Directly established by executable code, configuration, invocation paths, or multiple mutually reinforcing repository artifacts.

**Strongly inferred:** Supported by connected evidence, but the complete runtime path is not directly visible.

**Unverified:** Suggested by documentation, names, comments, or incomplete configuration without enough evidence to establish actual behavior.

**Apparently inactive/legacy:** Present in the repository but lacking a credible active execution path, or superseded by stronger evidence.

Do not upgrade intended behavior to verified implementation.

Do not convert a common framework convention into a repository fact.

## Distinguishing implementation detail from other phases

Do not turn this phase into Low-Level Design.

Low-Level Design asks:

"What internal code structures and interactions implement the system?"

Implementation Detail asks:

"How are those structures configured, assembled, executed, built, packaged, deployed, and operated?"

Do not turn this phase into Technology Architecture.

Technology Architecture asks:

"What major technologies and runtime boundaries exist?"

Implementation Detail asks:

"Where and how are those technologies concretely configured and invoked?"

Do not turn this phase into Testing Harness.

Testing Harness asks:

"How is behavior verified?"

Implementation Detail asks:

"How are tests configured and executed as part of the repository workflow?"

## Anti-patterns and rationalizations

| Rationalization                                                | Required response                                                                                                           |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| "The README says this is the startup command."                 | Confirm the command against package, script, container, or source entry-point evidence.                                     |
| "A dependency is installed, so the application uses it."       | Trace imports, initialization, or runtime consumers.                                                                        |
| "An environment variable exists, so it affects behavior."      | Find its loading and consumption path.                                                                                      |
| "A Dockerfile proves the production deployment."               | Establish whether deployment tooling actually uses the image.                                                               |
| "A CI workflow exists, so it is active."                       | Distinguish repository presence from triggering and current use.                                                            |
| "The framework handles startup automatically."                 | Identify the repository-specific bootstrap and registration mechanisms.                                                     |
| "An async function means background execution."                | Establish scheduling or concurrent execution.                                                                               |
| "A health-check endpoint proves production monitoring."        | Distinguish endpoint implementation from deployment-level probing or alerting.                                              |
| "A logging library means observability is implemented."        | Trace initialization and meaningful operational use.                                                                        |
| "A migration directory proves migrations run automatically."   | Identify the command, workflow, or deployment path that executes them.                                                      |
| "Configuration files define the actual environment."           | Distinguish examples, defaults, templates, and active deployment configuration.                                             |
| "The cleanest path is the intended path."                      | Describe the path actually supported by repository evidence.                                                                |
| "Every script must be documented."                             | Focus on scripts that materially participate in build, execution, testing, deployment, or operations.                       |
| "Missing deployment files mean the system cannot be deployed." | Report only what the repository does and does not evidence. External deployment processes may exist outside the repository. |

## Red flags

Investigate further when:

* startup behavior is inferred only from filenames
* documentation and executable configuration disagree
* multiple entry points exist without clear classification
* environment variables are listed but their consumers are unknown
* dependency declarations are mistaken for runtime integration
* build scripts exist but their outputs are unexplained
* container configuration conflicts with package scripts
* multiple configuration systems appear to coexist
* CI and local commands execute different paths
* migrations exist without an identified execution mechanism
* deployment manifests exist without an identified artifact source
* health checks are described without determining what they actually test
* observability claims are based only on installed libraries
* generated files are mistaken for hand-authored implementation
* development and production paths are silently conflated
* stale or alternate infrastructure may change the actual execution path

## Verification Gate

Before completing this phase, verify:

* [ ] The primary execution entry point has been identified or explicitly remains unknown.
* [ ] The bootstrap sequence has been reconstructed where repository evidence permits.
* [ ] Major configuration sources have been identified.
* [ ] Important configuration values have been traced to their consumers.
* [ ] Application composition and dependency initialization have been examined.
* [ ] Dependency management has been distinguished from actual runtime usage.
* [ ] Build and artifact-generation mechanisms have been examined where relevant.
* [ ] The local development execution path has been identified where relevant.
* [ ] Runtime processes or workers have been distinguished from internal modules.
* [ ] Background or asynchronous execution mechanisms have been traced where relevant.
* [ ] Persistence initialization and migration mechanics have been examined where relevant.
* [ ] External client initialization has been traced where relevant.
* [ ] Packaging or containerization has been examined where present.
* [ ] Deployment automation has been distinguished from merely present infrastructure files.
* [ ] Environment-specific behavior has been traced where relevant.
* [ ] Logging, diagnostics, metrics, tracing, and health mechanisms have been examined where present.
* [ ] Shutdown and recovery behavior has been examined where relevant.
* [ ] Test execution mechanics have been identified without duplicating the Testing Harness analysis.
* [ ] Generated, legacy, development-only, and apparently inactive artifacts have been considered.
* [ ] Documentation claims have been checked against executable evidence where possible.
* [ ] Facts, inferences, and unknowns are distinguishable.
* [ ] The result explains how the repository becomes a running system rather than merely describing its source code.

## Output expectations

Return a professional dossier-quality Implementation Detail analysis.

Organize the result around the concrete lifecycle of the software.

Start with how the repository is invoked and how control enters the application.

Then explain how configuration is loaded, dependencies are assembled, runtime components are initialized, and the system begins operating.

Describe build, packaging, testing, containerization, deployment, and operational mechanisms where evidence exists.

Identify important commands, scripts, entry points, configuration flows, runtime processes, and lifecycle boundaries precisely.

Include a focused Mermaid diagram when a startup sequence, process topology, build flow, deployment path, or configuration flow materially improves understanding.

Use repository artifacts as evidence.

Do not reproduce large source files.

Do not recommend refactoring or redesign.

Do not describe conventional framework behavior as a repository fact unless the implementation confirms it.

Explicitly identify important gaps in repository evidence rather than filling them with assumptions.

The completed analysis should allow a reader to answer:

"Exactly how does this repository move from source code and configuration to a built, initialized, running, testable, deployable, and observable software system?"
