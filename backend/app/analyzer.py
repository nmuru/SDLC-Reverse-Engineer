"""Repository analysis orchestration."""

import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from math import ceil
from pathlib import Path
from typing import Callable, Optional

from .agent_runner import run_phase_agent
from .config import settings
from .exporter import create_download_package

from .renderer import render_analysis


PHASES = [
    ("business-purpose", "Business Purpose"),
    ("features", "Features"),
    ("business-requirements", "Business Requirements"),
    ("software-requirements", "Software Requirements"),  
    ("technology-architecture", "Technology Architecture"),
    ("design-pattern", "Design Pattern"),
    ("high-level-design", "High-Level Design"),
    ("low-level-design", "Low-Level Design"),
    ("implementation-detail", "Implementation Detail"),
    ("testing-harness", "Testing Harness"),
    ("future-directions", "Future Directions"),
]


PhaseCompleteCallback = Callable[[dict], None]

def _run_single_phase(
    phase_key: str,
    phase_name: str,
    workspace: Path,
    repo_url: str,
    output_run_dir: Path,
    run_id: str,
    provider: str,
    model: str,
    api_key: str,
) -> dict:
    """
    Run one independent analysis phase.

    OpenCode produces the raw analytical output. The presentation renderer then
    reformats that complete output without repository access and without relying
    on a structured JSON contract from the analysis agent.
    """
    phase_workspace = workspace / phase_key
    phase_workspace.mkdir(parents=True, exist_ok=True)

    raw_result = run_phase_agent(
        phase=phase_key,
        phase_name=phase_name,
        workspace=phase_workspace,
        repo_url=repo_url,
        provider=provider,
        model=model,
        api_key=api_key,
    )

    if not raw_result or not raw_result.strip():
        raise RuntimeError(
            f"OpenCode returned an empty result for phase '{phase_key}'."
        )

    phase_output_dir = output_run_dir / phase_key
    phase_output_dir.mkdir(parents=True, exist_ok=True)

    # Preserve the exact OpenCode output for diagnosis and auditing.
    source_path = phase_output_dir / "opencode-output.md"
    source_path.write_text(
        raw_result,
        encoding="utf-8",
    )

    # The renderer receives the entire raw output. It is repository-blind and
    # performs only presentation work.
    rendered_result = render_analysis(
        phase=phase_key,
        analysis=raw_result,
        provider=provider,
        model=model,
        api_key=api_key,
    )

    if not rendered_result or not rendered_result.strip():
        raise RuntimeError(
            f"Renderer returned an empty result for phase '{phase_key}'."
        )

    # raw.md remains the existing application contract: this is the version
    # consumed by the frontend and exporter.
    raw_path = phase_output_dir / "raw.md"
    raw_path.write_text(
        rendered_result,
        encoding="utf-8",
    )

    return {
        "phase": phase_key,
        "phase_name": phase_name,
        "raw_analysis": rendered_result,
        "raw_path": str(raw_path),
        "run_id": run_id,
    }



def _run_batch(
    batch: list[tuple[str, str]],
    workspace: Path,
    repo_url: str,
    output_run_dir: Path,
    run_id: str,
    on_phase_complete: Optional[PhaseCompleteCallback] = None,
    provider: str = "openrouter",
    model: str = "stealth/ox-alpha",
    api_key: str = "",
) -> dict:
    """Run all phases in one batch concurrently."""

    batch_results = {}

    with ThreadPoolExecutor(max_workers=len(batch)) as executor:
        future_to_phase = {
            executor.submit(
                _run_single_phase,
                phase_key,
                phase_name,
                workspace,
                repo_url,
                output_run_dir,
                run_id,
                provider,
                model,
                api_key,
            ): phase_key
            for phase_key, phase_name in batch
        }

        first_error = None

        for future in as_completed(future_to_phase):
            phase_key = future_to_phase[future]

            try:
                phase_result = future.result()

                batch_results[phase_key] = phase_result

                # Publish each completed phase immediately. This callback
                # will later be connected to the streaming API/frontend.
                if on_phase_complete is not None:
                    on_phase_complete(phase_result)

            except Exception as exc:
                if first_error is None:
                    first_error = exc

        if first_error is not None:
            raise first_error

    return batch_results


def analyze_repository(
    repo_url: str,
    phases_per_batch: int = settings.phases_per_batch,
    number_of_batches: Optional[int] = None,
    batch_mode: str = settings.batch_mode,
    on_phase_complete: Optional[PhaseCompleteCallback] = None,
    selected_phases: Optional[list[str]] = None,
    work_id: Optional[str] = None,
    provider: str = "openrouter",
    model: str = "stealth/ox-alpha",
    api_key: Optional[str] = None,
) -> dict:
    """
    Run reverse-engineering phases in configurable batches.

    phases_per_batch:
        Number of independent phases in each batch.

    number_of_batches:
        Number of batches to execute.

    batch_mode:
        "parallel" runs all selected batches concurrently.
        "sequence" runs one batch at a time.

    Phases within every batch always run concurrently.

    A phase failure stops the overall analysis. Results from phases that
    completed successfully remain available.
    """

    if not repo_url or not repo_url.strip():
        raise ValueError("repo_url cannot be empty")
    if not provider or not provider.strip():
        raise ValueError("provider cannot be empty")
    if not model or not model.strip():
        raise ValueError("model cannot be empty")
    if not api_key or not api_key.strip():
        raise ValueError("api_key cannot be empty")
    if provider.strip().lower() not in {"openrouter", "openai", "anthropic", "google"}:
        raise ValueError(
            "Unsupported provider. Supported providers are: "
            "openrouter, openai, anthropic, google"
        )

    if phases_per_batch < 1:
        raise ValueError("phases_per_batch must be at least 1")

    if batch_mode not in {"parallel", "sequence"}:
        raise ValueError("batch_mode must be 'parallel' or 'sequence'")

    available_phase_ids = {phase_key for phase_key, _ in PHASES}
    if selected_phases is None:
        fallback_count = number_of_batches or 1
        selected_phase_ids = [
            phase_key
            for phase_key, _ in PHASES[: phases_per_batch * fallback_count]
        ]
    else:
        if not selected_phases:
            raise ValueError("selected_phases must contain at least one phase")
        if len(set(selected_phases)) != len(selected_phases):
            raise ValueError("selected_phases must not contain duplicates")
        unknown_phases = set(selected_phases) - available_phase_ids
        if unknown_phases:
            raise ValueError(
                "selected_phases contains unknown phases: "
                + ", ".join(sorted(unknown_phases))
            )
        selected_phase_ids = selected_phases

    phase_by_id = dict(PHASES)
    selected_phase_definitions = [
        (phase_key, phase_by_id[phase_key]) for phase_key in selected_phase_ids
    ]
    number_of_batches = ceil(len(selected_phase_definitions) / phases_per_batch)

    batches = [
        selected_phase_definitions[start : start + phases_per_batch]
        for start in range(0, len(selected_phase_definitions), phases_per_batch)
    ]

    results = {}
    run_id = work_id or uuid.uuid4().hex
    if not run_id.isalnum():
        raise ValueError("work_id must contain only letters and numbers")

    output_root = Path(settings.analysis_results_dir)
    if not output_root.is_absolute():
        output_root = Path(__file__).resolve().parents[1] / output_root

    output_run_dir = output_root / run_id
    output_run_dir.mkdir(parents=True, exist_ok=True)

    existing_phases = {
        phase_dir.name
        for phase_dir in output_run_dir.iterdir()
        if phase_dir.is_dir() and (phase_dir / "raw.md").is_file()
    }
    duplicate_phases = existing_phases.intersection(selected_phase_ids)
    if duplicate_phases:
        raise ValueError(
            "selected_phases already completed: "
            + ", ".join(sorted(duplicate_phases))
        )

    # OpenCode workspaces remain temporary; analysis results are persistent.
    with tempfile.TemporaryDirectory(prefix="reverse-engineer-") as tmp:
        workspace = Path(tmp)

        if batch_mode == "parallel":
            # All batches run concurrently.
            with ThreadPoolExecutor(max_workers=len(batches)) as executor:
                future_to_batch = {
                    executor.submit(
                        _run_batch,
                        batch,
                        workspace,
                        repo_url,
                        output_run_dir,
                        run_id,
                        on_phase_complete,
                        provider,
                        model,
                        api_key,
                    ): index
                    for index, batch in enumerate(batches)
                }

                first_error = None

                for future in as_completed(future_to_batch):
                    try:
                        batch_results = future.result()
                        results.update(batch_results)
                    except Exception as exc:
                        if first_error is None:
                            first_error = exc

                if first_error is not None:
                    raise first_error

        else:
            # Batches run sequentially; phases inside each batch remain concurrent.
            for batch in batches:
                batch_results = _run_batch(
                    batch,
                    workspace,
                    repo_url,
                    output_run_dir,
                    run_id,
                    on_phase_complete,
                    provider,
                    model,
                    api_key,
                )
                results.update(batch_results)

        # Create the offline package only after the final configured phase is persisted.
        create_download_package(output_run_dir)

    return {
        "run_id": run_id,
        "results": results,
    }