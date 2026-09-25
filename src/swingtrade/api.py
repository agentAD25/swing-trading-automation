from __future__ import annotations

from fastapi import FastAPI

from swingtrade.config import RuntimeConfig


def create_app(config: RuntimeConfig | None = None) -> FastAPI:
    runtime = config or RuntimeConfig()  # type: ignore[call-arg]
    app = FastAPI(title="SwingTrade Offline Foundation")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": runtime.mode.value}

    return app
