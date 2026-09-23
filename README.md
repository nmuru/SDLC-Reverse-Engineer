# SDLC Reverse Engineer

An AI-powered web application that reverse-engineers an existing software repository into a structured SDLC dossier.

The application analyzes a codebase and reconstructs:

- Business purpose
- Features
- Requirements
- Technology architecture
- High-level design
- Low-level design
- Implementation details
- Testing strategy
- Future directions

This is not intended to be generic code summarization. The analysis is evidence-driven: conclusions are grounded in repository artifacts and distinguish verified facts, reasonable inferences, and unknowns.

## Architecture

The application has two main components:

- **Frontend:** Next.js / React / TypeScript
- **Backend:** Python / FastAPI
- **AI execution:** OpenCode as the agent harness

The backend runs a sequential nine-phase analysis pipeline. Phase-specific methodologies are defined as OpenCode skills under `backend/.opencode/skills/`, while the application-level agent instructions are defined in `AGENTS.md`.

The analysis is designed to keep repository acquisition, agent logic, model/provider configuration, and phase-specific methodology conceptually separate.

## Analysis Pipeline

The dossier is produced through these phases:

1. Business Purpose
2. Features
3. Requirements
4. Technology Architecture
5. High-Level Design
6. Low-Level Design
7. Implementation Detail
8. Testing Harness
9. Future Directions

Each phase produces a presentation-ready documentation artifact. Later phases can use concise, structured handoffs from earlier phases while continuing to inspect the repository directly.

## Evidence-Driven Analysis

The system is designed to inspect concrete repository evidence such as:

- Source code and directory structure
- Package manifests and dependencies
- Configuration
- APIs and routes
- Schemas and database definitions
- Tests
- Deployment artifacts
- Existing documentation

The analysis explicitly distinguishes facts supported by repository evidence from inferences and unknowns. The target repository is treated as read-only during analysis.

## Running Locally

The repository includes a Windows startup script:

```bat
./start.bat
```

The script creates the backend Python virtual environment when required, installs backend dependencies, and starts the FastAPI and Next.js development servers.

> **Note:** The current `start.bat` contains environment-specific Windows paths. If those paths do not match your machine, edit the script before running it.

You will also need the project's required Python and Node.js tooling and a working OpenCode installation/configuration.

## Project Structure

```
.
├── AGENTS.md
├── backend/
│   ├── .opencode/
│   ├── app/
│   ├── export/
│   ├── output-content/
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── public/
│   ├── package.json
│   └── package-lock.json
├── export/
└── start.bat
```

## Design Intent

A central design principle of this project is to separate the analysis behavior from the application code as far as practical.

The application provides the execution harness and orchestration, while the agent instructions and skills define the methodology for each SDLC objective. This makes the analysis workflow extensible without embedding every analytical rule directly into application code.

## Output Contract

Each analysis phase returns a structured JSON object containing:

```json
{
  "phase": "<phase-id>",
  "documentation": "<complete Markdown documentation>"
}
```

The generated documentation is intended to be directly usable as professional SDLC documentation.

## Status

This repository contains the OpenCode-based implementation of the SDLC Reverse Engineer. It was developed as a rapid prototype demonstrating how an agentic harness can orchestrate repository analysis through specialized phase skills.

## License

See the repository for licensing information.
