import logging
import asyncio
import json
from queue import Queue
from threading import Thread
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from .agent_runner import AgentRunnerError
from .analyzer import analyze_repository
from .config import settings
from .schemas import AnalyzeRequest


logger = logging.getLogger(__name__)

app = FastAPI(
    title="ReverseEngineer-SDLC API",
    version="0.2.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.allowed_origins.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/analysis/{work_id}/download")
def download_analysis(work_id: str) -> FileResponse:
    """Return the ZIP created when the requested analysis completed."""
    if Path(work_id).name != work_id:
        raise HTTPException(status_code=404, detail="Analysis download not found")

    output_root = Path(settings.analysis_results_dir)
    if not output_root.is_absolute():
        output_root = Path(__file__).resolve().parents[1] / output_root

    zip_path = output_root / work_id / "sdlc-documentation.zip"
    if not zip_path.is_file():
        raise HTTPException(status_code=404, detail="Analysis download not found")

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename="sdlc-documentation.zip",
    )


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest) -> StreamingResponse:
    """Run the analysis pipeline and stream completed phases to the frontend."""

    repo_url = str(request.repo_url)
    event_queue: Queue[dict[str, Any]] = Queue()

    def on_phase_complete(phase_result: dict) -> None:
        """Receive a completed phase and make it available to the stream."""
        event_queue.put(
            {
                "type": "phase_completed",
                "phase": phase_result["phase"],
                "phase_name": phase_result["phase_name"],
                "raw_analysis": phase_result["raw_analysis"],
                "raw_path": phase_result["raw_path"],
                "run_id": phase_result["run_id"],
            }
        )

    def run_analysis() -> None:
        """Run analysis in a background thread so the HTTP stream stays open."""
        api_key = request.api_key or settings.openrouter_api_key

        if not api_key:
            raise ValueError("OpenRouter API key is required.")
        
        try:
            results = analyze_repository(
            repo_url,
            phases_per_batch=settings.phases_per_batch,
            batch_mode=settings.batch_mode,
            selected_phases=request.selected_phases,
            work_id=request.work_id,
            on_phase_complete=on_phase_complete,
            provider=request.provider,
            model=request.model,
            api_key=api_key,
        )
            

            event_queue.put(
                {
                    "type": "analysis_completed",
                    "repo_url": repo_url,
                    "run_id": results["run_id"],
                    "completed_phases": list(results["results"].keys()),
                }
            )

        except AgentRunnerError as exc:
            # AgentRunnerError messages are intentionally sanitized in the
            # execution layer and are safe to return to the browser.
            event_queue.put(
                {
                    "type": "analysis_failed",
                    "repo_url": repo_url,
                    "error": str(exc),
                }
            )

        except ValueError as exc:
            # Validation errors are safe to return and contain no credentials.
            event_queue.put(
                {
                    "type": "analysis_failed",
                    "repo_url": repo_url,
                    "error": str(exc),
                }
            )

        except Exception:
            # Log the traceback on the server for diagnosis, but never include
            # the request object or API key explicitly in the log message and
            # never return raw exception text to the browser.
            logger.exception(
                "Unexpected analysis failure: repo_url=%s",
                repo_url,
            )
            event_queue.put(
                {
                    "type": "analysis_failed",
                    "repo_url": repo_url,
                    "error": (
                        "Analysis failed due to an unexpected backend error. "
                        "Please try again."
                    ),
                }
            )

    thread = Thread(
        target=run_analysis,
        daemon=True,
    )
    thread.start()

    async def event_stream():
        while True:
            event = await asyncio.to_thread(event_queue.get)

            yield (
                f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            )

            if event["type"] in {
                "analysis_completed",
                "analysis_failed",
            }:
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )