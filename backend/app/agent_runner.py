"""OpenCode phase runner."""

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
    target_opencode = workspace / ".opencode"
    target_opencode.mkdir(parents=True, exist_ok=True)

    if OPENCODE_SOURCE.exists():
        shutil.copytree(OPENCODE_SOURCE, target_opencode, dirs_exist_ok=True)

    if AGENTS_SOURCE.exists():
        shutil.copy2(AGENTS_SOURCE, workspace / "AGENTS.md")


def _copy_smoke_test_agent(workspace: Path) -> None:
    source_agent = OPENCODE_SOURCE / "agents" / f"{SMOKE_AGENT_NAME}.md"
    if not source_agent.is_file():
        raise AgentRunnerError(
            f"Smoke-test agent definition was not found: {source_agent}"
        )

    target_agents = workspace / ".opencode" / "agents"
    target_agents.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_agent, target_agents / source_agent.name)


def _write_dynamic_opencode_config(
    workspace: Path,
    repo_url: str,
    provider: str,
    model: str,
) -> None:
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
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def _write_smoke_test_opencode_config(
    workspace: Path,
    provider: str,
    model: str,
) -> None:
    config_path = workspace / "opencode.json"
    config = {
        "$schema": "https://opencode.ai/config.json",
        "model": _opencode_model_identifier(provider, model),
    }
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def _write_smoke_test_prompt_file(workspace: Path) -> None:
    """Keep the smoke-test task visible as a workspace artifact for diagnostics."""
    (workspace / ".smoke-test-prompt.txt").write_text(
        "Hi\n", encoding="utf-8"
    )


def _log_smoke_workspace(workspace: Path, agent_name: str, prompt: str) -> None:
    files = [
        str(path.relative_to(workspace))
        for path in sorted(workspace.rglob("*"))
        if path.is_file()
    ]

    config_path = workspace / "opencode.json"
    config_text = (
        config_path.read_text(encoding="utf-8")
        if config_path.is_file()
        else "<missing>"
    )

    agents_md_path = workspace / "AGENTS.md"
    diagnostic = (
        "\n===== PIPELINE SMOKE-TEST WORKSPACE ====="
        f"\nworkspace: {workspace}"
        f"\nagent: {agent_name}"
        f"\nprompt: {prompt!r}"
        f"\nAGENTS.md present: {agents_md_path.exists()}"
        "\nfiles:"
        + "".join(f"\n  - {file}" for file in files)
        + f"\nopencode.json:\n{config_text}"
        + "\n===== END PIPELINE SMOKE-TEST WORKSPACE =====\n"
    )
    print(diagnostic, flush=True)
    logger.warning(diagnostic)


def _opencode_model_identifier(provider: str, model: str) -> str:
    return f"{provider.strip().lower()}/{model.strip()}"


def _resolve_opencode_executable(opencode_executable: str) -> str:
    if os.path.isfile(opencode_executable):
        return opencode_executable
    resolved_opencode = shutil.which(
        "opencode.cmd" if os.name == "nt" else opencode_executable
    )
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
    env_name = provider_env_names.get(provider.strip().lower())
    if not env_name:
        raise AgentRunnerError(f"Unsupported provider '{provider}'.")
    return env_name


def _redact_diagnostic(value: str, api_key: Optional[str], command_env: dict[str, str]) -> str:
    if not value:
        return ""
    redacted = value
    for secret in {
        api_key.strip() if api_key else "",
        command_env.get("OPENROUTER_API_KEY", ""),
        command_env.get("OPENAI_API_KEY", ""),
        command_env.get("ANTHROPIC_API_KEY", ""),
        command_env.get("GOOGLE_GENERATIVE_AI_API_KEY", ""),
    }:
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
    """Run a phase through OpenCode. Smoke mode is temporarily the only active path."""
    workspace.mkdir(parents=True, exist_ok=True)
    _ensure_git_worktree(workspace)

    smoke_test = settings.pipeline_smoke_test

    # Temporary smoke-test-only harness. The normal production path is deliberately
    # disabled while we isolate OpenCode/OpenRouter behavior.
    if not smoke_test:
        raise AgentRunnerError(
            "PIPELINE_SMOKE_TEST must be true while the temporary smoke-test harness is active."
        )

    _copy_smoke_test_agent(workspace)
    _write_smoke_test_opencode_config(workspace, provider, model)
    _write_smoke_test_prompt_file(workspace)
    prompt = "Hi"
    agent_name = SMOKE_AGENT_NAME
    _log_smoke_workspace(workspace, agent_name, prompt)

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
        raise AgentRunnerError("An API key is required for the selected provider.")

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

    return raw_output
