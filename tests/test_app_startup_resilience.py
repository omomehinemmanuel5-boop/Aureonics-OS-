from pathlib import Path

import app.main as app_main


def test_render_start_command_uses_port_env_variable():
    render_yaml = Path("render.yaml").read_text(encoding="utf-8")
    assert "startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT" in render_yaml


def test_health_endpoint_survives_optional_dependency_failures(monkeypatch):
    original_import = app_main.importlib.import_module

    def failing_import(name, package=None):
        if name in {
            "app.database",
            "app.core_lock",
            "sovereign_kernel_v2",
            "app.controllers.routes",
            "app.controllers.simulation_routes",
            "app.controllers.cbf_routes",
        }:
            raise RuntimeError(f"simulated startup failure for {name}")
        return original_import(name, package)

    monkeypatch.setattr(app_main.importlib, "import_module", failing_import)
    app_main._load_runtime_dependencies()
    payload = app_main.praxis_health()

    assert payload["status"] == "ok"
    assert payload["kernel_ready"] is False
    assert payload["startup_errors"]
