"""
OpenCode phase runner.

The runner creates only a lightweight project workspace. In normal mode the
analysis agent receives the target Git repository as an OpenCode reference. In
pipeline smoke-test mode it uses an isolated no-tool agent and sends only a
minimal request through the same OpenCode and model-provider path.
"""

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPENCODE_SOURCE = PROJECT_ROOT / ".opencode"
AGENTS_SOURCE = PROJECT_ROOT.parent / "AGENTS.md"
SMOKE_AGENT_NAME = "pipeline-smoke-test"
SMOKE_TEST_RESPONSE = "SMOKE_TEST_OK"


class AgentRunnerError(RuntimeError):
    """Raised when an OpenCode phase cannot be completed."""


def _ensure_git_worktree(workspace: Path) -> None:
    """Initialize the temporary workspace when it is not a Git worktree."""
    check = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        check=False,
    )

    if check.returncode == 0 and check.stdout.strip() == "true":
        return

    try:
        subprocess.run(
            ["git", "init"],
            cwd=str(workspace),
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AgentRunnerError(
            f"Could not initialize temporary Git workspace: {workspace}"
        ) from exc


def _copy_normal_project_instructions(workspace: Path) -> None:
    """Copy the complete production OpenCode configuration into a workspace."""
    target_opencode = workspace / ".opencode"
    target_opencode.mkdir(parents=True, exist_ok=True)

    if OPENCODE_SOURCE.exists():
        shutil.copytree(OPENCODE_SOURCE, target_opencode, dirs_exist_ok=True)

    if AGENTS_SOURCE.exists():
        shutil.copy2(AGENTS_SOURCE, workspace / "AGENTS.md")


def _copy_smoke_test_agent(workspace: Path) -> None:
    """Copy only the isolated smoke-test agent into a sterile workspace."""
    source_agent = OPENCODE_SOURCE / "agents" / f"{SMOKE_AGENT_NAME}.md"
    if not source_agent.is_file():
        raise AgentRunnerError(
            f"Smoke-test agent definition was not found: {source_agent}"
        )

    target_agents = workspace / ".opencode" / "agents"
    target_agents.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_agent, target_agents / source_agent.name)


def _write_handoff(workspace: Path, previous_output: Optional[str]) -> None:
    """Write the previous phase result for continuity across normal phases."""
    handoff = workspace / ".reverse-engineer-handoff.md"

    if previous_output:
        handoff.write_text(
            "# Previous Phase Analysis\n\n"
            "The following is the completed analysis from the previous phase. "
            "Use it as context, but verify important claims against the "
            "repository evidence.\n\n"
            + previous_output,
            encoding="utf-8",
        )
    elif handoff.exists():
        handoff.unlink()


def _write_dynamic_opencode_config(
    workspace: Path,
    repo_url: str,
    provider: str,
    model: str,
) -> None:
    """Create the production project-level OpenCode configuration."""
    config_path = workspace / "opencode.json"
    config = {
        "$schema": "https://opencode.ai/config.json",
        "model": _opencode_model_identifier(provider, model),
        "references": {
            "target-repository": {
                "repository": repo_url.strip(),
                "description": (
                    "The target repository being reverse engineered. "
                    "Inspect this reference as the authoritative source "
                    "for repository analysis."
                ),
            }
        },
    }

    config_path.write_text(
        json.dumps(config, indent=2) + "\n",
        encoding="utf-8",
    )


def _write_smoke_test_opencode_config(
    workspace: Path,
    provider: str,
    model: str,
) -> None:
    """Create a minimal OpenCode configuration without repository references."""
    config_path = workspace / "opencode.json"
    config = {
        "$schema": "https://opencode.ai/config.json",
        "model": _opencode_model_identifier(provider, model),
    }

    config_path.write_text(
        json.dumps(config, indent=2) + "\n",
        encoding="utf-8",
    )


def _opencode_model_identifier(provider: str, model: str) -> str:
    """Convert the provider/model selection into the identifier OpenCode expects."""
    normalized_provider = provider.strip().lower()
    normalized_model = model.strip()
    return f"{normalized_provider}/{normalized_model}"


def _resolve_opencode_executable(opencode_executable: str) -> str:
    if os.path.isfile(opencode_executable):
        return opencode_executable
    if os.name == "nt":
        resolved_opencode = shutil.which("opencode.cmd")
    else:
        resolved_opencode = shutil.which(opencode_executable)
    if not resolved_opencode:
        raise AgentRunnerError(
            f"OpenCode executable '{opencode_executable}' was not found."
        )
    return resolved_opencode


def _provider_environment_name(provider: str) -> str:
    provider_env_names = {
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_GENERATIVE_AI_API_KEY",
    }
    normalized_provider = provider.strip().lower()
    env_name = provider_env_names.get(normalized_provider)
    if not env_name:
        raise AgentRunnerError(
            f"Unsupported provider '{provider}'. "
            "Use a supported provider or add explicit credential handling."
        )
    return env_name


def _redact_diagnostic(value: str, api_key: Optional[str], command_env: dict[str, str]) -> str:
    if not value:
        return ""
    redacted = value
    secrets_to_redact = [
        api_key.strip() if api_key else "",
        command_env.get("OPENROUTER_API_KEY", ""),
        command_env.get("OPENAI_API_KEY", ""),
        command_env.get("ANTHROPIC_API_KEY", ""),
        command_env.get("GOOGLE_GENERATIVE_AI_API_KEY", ""),
    ]
    for secret in secrets_to_redact:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    return redacted


def run_phase_agent(
    phase: str,
    phase_name: str,
    workspace: Path,
    repo_url: str,
    previous_output: Optional[str] = None,
    opencode_executable: str = os.getenv("OPENCODE_EXECUTABLE", "opencode"),
    provider: str = "openrouter",
    model: str = "z-ai/glm-5.3-flash",
    api_key: Optional[str] = None,
) -> str:
    """Run one phase through the normal analysis agent or smoke-test agent."""
    workspace.mkdir(parents=True, exist_ok=True)
    _ensure_git_worktree(workspace)

    smoke_test = settings.pipeline_smoke_test

    if smoke_test:
        _copy_smoke_test_agent(workspace)
        _write_smoke_test_opencode_config(workspace, provider, model)
        prompt = "Run the pipeline connectivity smoke test."
        agent_name = SMOKE_AGENT_NAME
    else:
        _copy_normal_project_instructions(workspace)
        _write_dynamic_opencode_config(workspace, repo_url, provider, model)
        _write_handoff(workspace, previous_output)
        prompt = f"""
Perform the "{phase_name}" phase of the repository reverse-engineering workflow.

Before beginning the analysis, invoke the native OpenCode skill tool exactly
once with this exact skill name:

skill({{ name: "{phase}" }})

Do not manually read the SKILL.md file instead of invoking the native skill
tool. Do not begin the phase analysis until that skill has been loaded.

The target repository is available through the OpenCode reference
"target-repository". Inspect that repository directly and use the
phase-specific skill for this phase.

Treat repository evidence as authoritative. The previous-phase handoff is
supporting context only and must not be accepted blindly.

Complete the full phase analysis. Do not provide a short summary merely
because the phase has been identified. Follow the loaded skill's
investigation workflow and output requirements.

FINAL OUTPUT:

Return the complete final SDLC documentation for this phase as normal Markdown.

Do not wrap the final documentation in JSON. Do not use a JSON envelope.
Do not require fields such as "phase" or "documentation".

The final response may contain headings, paragraphs, tables, lists, code
blocks, and Mermaid diagrams when required by the loaded phase skill. The
analysis pipeline will preserve this complete raw output and pass it to a
separate presentation renderer.

Perform all repository exploration, tool usage, evidence gathering,
verification, and reasoning before producing the final response.

Do not provide a short summary merely because the phase has been identified.
Follow the loaded skill's investigation workflow and output requirements.

This is a read-only documentation task. Do not modify the target repository.
""".strip()
        agent_name = "reverse-engineer"

    resolved_opencode = _resolve_opencode_executable(opencode_executable)
    opencode_model = _opencode_model_identifier(provider, model)

    command = [
        resolved_opencode,
        "run",
        "--dir",
        str(workspace),
        "--agent",
        agent_name,
        "--auto",
        "--model",
        opencode_model,
        prompt,
    ]

    command_env = os.environ.copy()
    env_name = _provider_environment_name(provider)

    if not api_key or not api_key.strip():
        raise AgentRunnerError(
            "An API key is required for the selected provider."
        )

    command_env[env_name] = api_key.strip()

    try:
        result = subprocess.run(
            command,
            cwd=str(workspace),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            env=command_env,
        )
    except OSError as exc:
        raise AgentRunnerError(
            f"Could not start OpenCode during phase '{phase}': {exc}"
        ) from exc

    if result.returncode != 0:
        stderr = _redact_diagnostic(result.stderr.strip(), api_key, command_env)
        stdout = _redact_diagnostic(result.stdout.strip(), api_key, command_env)
        diagnostic = (
            "\n===== OpenCode sanitized diagnostic ====="
            f"\nphase: {phase}"
            f"\nprovider: {provider}"
            f"\nmodel: {opencode_model}"
            f"\nsmoke_test: {smoke_test}"
            f"\nreturncode: {result.returncode}"
            f"\nstderr: {stderr[:4000] or '<empty>'}"
            f"\nstdout: {stdout[:4000] or '<empty>'}"
            "\n===== End OpenCode diagnostic =====\n"
        )
        print(diagnostic, flush=True)
        logger.error(diagnostic)
        raise AgentRunnerError(
            f"OpenCode failed during phase '{phase}'. "
            "Check the backend logs for a sanitized diagnostic."
        )

    raw_output = result.stdout.strip()
    if not raw_output:
        raise AgentRunnerError(
            f"OpenCode completed phase '{phase}' but returned an empty final output."
        )

    if smoke_test and raw_output != SMOKE_TEST_RESPONSE:
        raise AgentRunnerError(
            f"Smoke-test agent returned an unexpected response for phase '{phase}': "
            f"{raw_output[:200]!r}"
        )

    return raw_output
