"""OpenCode phase runner."""

import json
import logging
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

import requests

from .config import settings

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPENCODE_SOURCE = PROJECT_ROOT / ".opencode"
AGENTS_SOURCE = PROJECT_ROOT.parent / "AGENTS.md"
SMOKE_AGENT_NAME = "pipeline-smoke-test"


class AgentRunnerError(RuntimeError):
    """Raised when an OpenCode phase cannot be completed."""


def _ensure_git_worktree(workspace: Path) -> None:
    check = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"], cwd=str(workspace),
        capture_output=True, text=True, check=False,
    )
    if check.returncode == 0 and check.stdout.strip() == "true":
        return
    try:
        subprocess.run(["git", "init"], cwd=str(workspace), capture_output=True,
                       text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AgentRunnerError(f"Could not initialize temporary Git workspace: {workspace}") from exc


def _copy_smoke_test_agent(workspace: Path) -> None:
    source_agent = OPENCODE_SOURCE / "agents" / f"{SMOKE_AGENT_NAME}.md"
    if not source_agent.is_file():
        raise AgentRunnerError(f"Smoke-test agent definition was not found: {source_agent}")
    target_agents = workspace / ".opencode" / "agents"
    target_agents.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_agent, target_agents / source_agent.name)


def _opencode_model_identifier(provider: str, model: str) -> str:
    provider_name = provider.strip().lower()
    model_name = model.strip()
    if model_name.lower().startswith(f"{provider_name}/"):
        return model_name
    return f"{provider_name}/{model_name}"


def _write_smoke_test_opencode_config(workspace: Path, provider: str, model: str) -> None:
    config = {"$schema": "https://opencode.ai/config.json", "model": _opencode_model_identifier(provider, model)}
    (workspace / "opencode.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def _write_smoke_test_prompt_file(workspace: Path) -> None:
    (workspace / ".smoke-test-prompt.txt").write_text("Hi\n", encoding="utf-8")


def _log_smoke_workspace(workspace: Path, agent_name: str, prompt: str) -> None:
    files = [str(path.relative_to(workspace)) for path in sorted(workspace.rglob("*")) if path.is_file()]
    config_path = workspace / "opencode.json"
    config_text = config_path.read_text(encoding="utf-8") if config_path.is_file() else "<missing>"
    diagnostic = ("\n===== PIPELINE SMOKE-TEST WORKSPACE =====" f"\nworkspace: {workspace}"
                  f"\nagent: {agent_name}" f"\nprompt: {prompt!r}"
                  f"\nconfigured PIPELINE_SMOKE_TEST: {settings.pipeline_smoke_test}"
                  f"\nAGENTS.md present: {(workspace / 'AGENTS.md').exists()}" "\nfiles:"
                  + "".join(f"\n  - {file}" for file in files) + f"\nopencode.json:\n{config_text}"
                  + "\n===== END PIPELINE SMOKE-TEST WORKSPACE =====\n")
    print(diagnostic, flush=True)
    logger.warning(diagnostic)


def _resolve_opencode_executable(opencode_executable: str) -> str:
    if os.path.isfile(opencode_executable):
        return opencode_executable
    resolved = shutil.which("opencode.cmd" if os.name == "nt" else opencode_executable)
    if not resolved:
        raise AgentRunnerError(f"OpenCode executable '{opencode_executable}' was not found.")
    return resolved


def _provider_environment_name(provider: str) -> str:
    names = {"openrouter": "OPENROUTER_API_KEY", "openai": "OPENAI_API_KEY",
             "anthropic": "ANTHROPIC_API_KEY", "google": "GOOGLE_GENERATIVE_AI_API_KEY"}
    env_name = names.get(provider.strip().lower())
    if not env_name:
        raise AgentRunnerError(f"Unsupported provider '{provider}'.")
    return env_name


def _redact_diagnostic(value: str, api_key: Optional[str], command_env: dict[str, str]) -> str:
    redacted = value or ""
    for secret in {api_key.strip() if api_key else "", command_env.get("OPENROUTER_API_KEY", ""),
                   command_env.get("OPENAI_API_KEY", ""), command_env.get("ANTHROPIC_API_KEY", ""),
                   command_env.get("GOOGLE_GENERATIVE_AI_API_KEY", "")}:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    return redacted


_SERVER_URL = os.getenv("OPENCODE_SERVER_URL", "http://127.0.0.1:4096").rstrip("/")
_SERVER_LOCK = threading.Lock()
_SERVER_PROCESS: Optional[subprocess.Popen] = None
_SERVER_STDERR_PATH = PROJECT_ROOT / "opencode-server-stderr.log"


def _server_healthcheck(url: str) -> bool:
    try:
        return requests.get(f"{url}/global/health", timeout=2).ok
    except requests.RequestException:
        return False


def _server_error_text(response: requests.Response) -> str:
    return response.text.strip()[:4000] or "<empty response body>"


def _ensure_opencode_server(*, resolved_executable: str, api_key: str, provider: str, workspace: Path) -> str:
    global _SERVER_PROCESS
    with _SERVER_LOCK:
        if _server_healthcheck(_SERVER_URL):
            return _SERVER_URL
        if _SERVER_PROCESS is not None and _SERVER_PROCESS.poll() is None:
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if _server_healthcheck(_SERVER_URL):
                    return _SERVER_URL
                time.sleep(0.25)
        env = os.environ.copy()
        env[_provider_environment_name(provider)] = api_key.strip()
        port = _SERVER_URL.rsplit(":", 1)[-1]
        command = [resolved_executable, "serve", "--hostname", "127.0.0.1", "--port", port]
        try:
            handle = open(_SERVER_STDERR_PATH, "w", encoding="utf-8")
            _SERVER_PROCESS = subprocess.Popen(command, cwd=str(workspace), env=env, stdout=handle, stderr=handle)
        except OSError as exc:
            raise AgentRunnerError(f"Could not start OpenCode server: {exc}") from exc
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if _server_healthcheck(_SERVER_URL):
                return _SERVER_URL
            if _SERVER_PROCESS.poll() is not None:
                raise AgentRunnerError(f"OpenCode server exited before becoming ready. See {_SERVER_STDERR_PATH}.")
            time.sleep(0.25)
        _SERVER_PROCESS.terminate()
        _SERVER_PROCESS = None
        raise AgentRunnerError("OpenCode server did not become ready within 15 seconds.")


def _server_smoke_phase(*, server_url: str, workspace: Path, phase: str, provider: str, model: str, prompt: str) -> str:
    response = requests.post(f"{server_url}/session", json={"title": f"reverse-sdlc-smoke-{phase}"}, timeout=15)
    if not response.ok:
        raise AgentRunnerError(f"OpenCode server could not create a session for phase '{phase}': HTTP {response.status_code}: {_server_error_text(response)}")
    session = response.json()
    session_id = session.get("id") or session.get("sessionID")
    if not session_id:
        raise AgentRunnerError(f"OpenCode server did not return a session id for phase '{phase}'.")

    provider_id, model_id = model.split("/", 1)
    response = requests.post(
        f"{server_url}/session/{session_id}/message",
        json={
            "agent": SMOKE_AGENT_NAME,
            "model": {"providerID": provider_id, "modelID": model_id},
            "parts": [{"type": "text", "text": prompt}],
        },
        timeout=300,
    )
    if not response.ok:
        server_log = ""
        try:
            if _SERVER_STDERR_PATH.exists():
                server_log = _SERVER_STDERR_PATH.read_text(encoding="utf-8", errors="replace")[-4000:]
        except OSError:
            server_log = "<could not read server log>"
        raise AgentRunnerError(f"OpenCode server failed phase '{phase}': HTTP {response.status_code}; response: {_server_error_text(response)}; server log: {server_log or '<empty>'}")

    data = response.json() if response.content else {}
    parts = data.get("parts", []) if isinstance(data, dict) else []
    text = "\n".join(part.get("text", "") for part in parts if isinstance(part, dict) and isinstance(part.get("text"), str)).strip()
    if not text and isinstance(data, dict):
        message = data.get("message") or {}
        for part in message.get("parts", []) if isinstance(message, dict) else []:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                text += ("\n" if text else "") + part["text"].strip()
    if not text and isinstance(data.get("content") if isinstance(data, dict) else None, str):
        text = data["content"].strip()
    if not text:
        raise AgentRunnerError(f"OpenCode server returned an empty response for phase '{phase}'.")
    return text


def run_phase_agent(phase: str, phase_name: str, workspace: Path, repo_url: str,
                    previous_output: Optional[str] = None,
                    opencode_executable: str = os.getenv("OPENCODE_EXECUTABLE", "opencode"),
                    provider: str = "openrouter", model: str = "z-ai/glm-5.3-flash",
                    api_key: Optional[str] = None) -> str:
    del repo_url, previous_output, phase_name
    workspace.mkdir(parents=True, exist_ok=True)
    _ensure_git_worktree(workspace)
    _copy_smoke_test_agent(workspace)
    _write_smoke_test_opencode_config(workspace, provider, model)
    _write_smoke_test_prompt_file(workspace)
    prompt = "Hi"
    _log_smoke_workspace(workspace, SMOKE_AGENT_NAME, prompt)
    resolved_opencode = _resolve_opencode_executable(opencode_executable)
    if not api_key or not api_key.strip():
        raise AgentRunnerError("An API key is required for the selected provider.")
    if settings.pipeline_smoke_test:
        opencode_model = _opencode_model_identifier(provider, model)
        try:
            server_url = _ensure_opencode_server(resolved_executable=resolved_opencode, api_key=api_key, provider=provider, workspace=workspace)
            return _server_smoke_phase(server_url=server_url, workspace=workspace, phase=phase, provider=provider, model=opencode_model, prompt=prompt)
        except requests.RequestException as exc:
            raise AgentRunnerError(f"OpenCode server request failed during phase '{phase}': {exc}") from exc
    env = os.environ.copy()
    env[_provider_environment_name(provider)] = api_key.strip()
    opencode_model = _opencode_model_identifier(provider, model)
    command = [resolved_opencode, "run", "--dir", str(workspace), "--agent", SMOKE_AGENT_NAME, "--auto", "--model", opencode_model, prompt]
    try:
        result = subprocess.run(command, cwd=str(workspace), capture_output=True, text=True, encoding="utf-8", errors="replace", check=False, env=env)
    except OSError as exc:
        raise AgentRunnerError(f"Could not start OpenCode during phase '{phase}': {exc}") from exc
    if result.returncode != 0:
        stderr = _redact_diagnostic(result.stderr.strip(), api_key, env)
        stdout = _redact_diagnostic(result.stdout.strip(), api_key, env)
        diagnostic = ("\n===== OpenCode sanitized diagnostic =====" f"\nphase: {phase}" f"\nprovider: {provider}" f"\nmodel: {opencode_model}" f"\nconfigured PIPELINE_SMOKE_TEST: {settings.pipeline_smoke_test}" f"\nreturncode: {result.returncode}" f"\nstderr: {stderr[:4000] or '<empty>'}" f"\nstdout: {stdout[:4000] or '<empty>'}" "\n===== End OpenCode diagnostic =====\n")
        print(diagnostic, flush=True)
        logger.error(diagnostic)
        raise AgentRunnerError(f"OpenCode failed during phase '{phase}'. Check the backend logs for a sanitized diagnostic.")
    raw_output = result.stdout.strip()
    if not raw_output:
        raise AgentRunnerError(f"OpenCode completed phase '{phase}' but returned an empty final output.")
    return raw_output
