"""
OpenCode phase runner.

The runner creates only a lightweight project workspace. The target Git
repository is supplied to OpenCode as a Git reference rather than being
cloned by this application.
"""

import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional
import json

from .config import settings

logger = logging.getLogger(__name__)
print("LOADED: CURRENT agent_runner.py", flush=True)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPENCODE_SOURCE = PROJECT_ROOT / ".opencode"
AGENTS_SOURCE = PROJECT_ROOT.parent / "AGENTS.md"


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


def _copy_project_instructions(workspace: Path) -> None:
    """Copy the local OpenCode configuration/instructions into the workspace."""
    target_opencode = workspace / ".opencode"
    target_opencode.mkdir(parents=True, exist_ok=True)

    if OPENCODE_SOURCE.exists():
        shutil.copytree(OPENCODE_SOURCE, target_opencode, dirs_exist_ok=True)

    if AGENTS_SOURCE.exists():
        shutil.copy2(AGENTS_SOURCE, workspace / "AGENTS.md")


def _write_handoff(workspace: Path, previous_output: Optional[str]) -> None:
    """Write the previous phase result for continuity across phases."""
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
    """
    Create the minimal project-level OpenCode config.

    The target repository is exposed as a named Git reference. OpenCode
    materializes the full repository in its managed repository cache.
    """
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



def _opencode_model_identifier(provider: str, model: str) -> str:
    """
    Convert the frontend provider/model selection into the identifier expected
    by OpenCode.
    """
    normalized_provider = provider.strip().lower()
    normalized_model = model.strip()

    return f"{normalized_provider}/{normalized_model}"


def run_phase_agent(
    phase: str,
    phase_name: str,
    workspace: Path,
    repo_url: str,
    previous_output: Optional[str] = None,
    opencode_executable: str = "opencode",
    provider: str = "openrouter",
    model: str = "z-ai/glm-5.3-flash",
    api_key: Optional[str] = None,
) -> str:
    """
    Run one phase of the reverse-engineering workflow.

    OpenCode starts in the lightweight workspace and accesses the target
    repository through the configured Git reference.
    """
    workspace.mkdir(parents=True, exist_ok=True)
    _ensure_git_worktree(workspace)

    _copy_project_instructions(workspace)
    _write_dynamic_opencode_config(workspace, repo_url, provider, model)
    _write_handoff(workspace, previous_output)

    prompt = f"""
Perform the "{phase_name}" phase of the repository reverse-engineering
workflow.

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

    if os.name == "nt":
        resolved_opencode = shutil.which("opencode.cmd")
    else:
        resolved_opencode = shutil.which(opencode_executable)

    if not resolved_opencode:
        raise AgentRunnerError(
            f"OpenCode executable '{opencode_executable}' was not found in PATH."
        )

    opencode_model = _opencode_model_identifier(provider, model)

    command = [
        resolved_opencode,
        "run",
        "--dir",
        str(workspace),
        "--agent",
        "reverse-engineer",
        "--auto",
        "--model",
        opencode_model,
        prompt,
    ]

    # Pass the user-supplied credential only to the child process environment.
    # Never put it in the command line, OpenCode config, workspace, prompt,
    # persisted analysis results, or application logs.
    command_env = os.environ.copy()
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
        # Redact the supplied key before any diagnostic leaves process memory.
        def redact(value: str) -> str:
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

        stderr = redact(result.stderr.strip())
        stdout = redact(result.stdout.strip())

        diagnostic = (
            "\n===== OpenCode sanitized diagnostic ====="
            f"\nphase: {phase}"
            f"\nprovider: {provider}"
            f"\nmodel: {opencode_model}"
            f"\nreturncode: {result.returncode}"
            f"\nstderr: {stderr[:4000] or '<empty>'}"
            f"\nstdout: {stdout[:4000] or '<empty>'}"
            "\n===== End OpenCode diagnostic =====\n"
        )

        # print() is intentional: it guarantees visibility in the Uvicorn console
        # even if Python logging configuration is overridden by the host.
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

    # The OpenCode result is intentionally returned without JSON parsing.
    # OpenCode is the repository-analysis agent and may produce rich Markdown,
    # Mermaid blocks, tables, and other natural documentation. A separate
    # renderer performs presentation cleanup after this stage.
    return raw_output
