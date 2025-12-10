import importlib.util
from pathlib import Path

import builtins
import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "tircorder-linux.py"


def load_launcher_module():
    spec = importlib.util.spec_from_file_location("tircorder_linux", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_choose_server_script_prefers_provided(tmp_path):
    module = load_launcher_module()
    script = tmp_path / "server_a.py"
    script.write_text("print('hi')", encoding="utf-8")

    chosen = module.choose_server_script(str(script))

    assert chosen == str(script)


def test_choose_server_script_prompts(monkeypatch):
    module = load_launcher_module()
    monkeypatch.setattr(
        module, "available_server_scripts", lambda: ["srv0.py", "srv1.py"]
    )
    monkeypatch.setattr(builtins, "input", lambda _: "1")

    chosen = module.choose_server_script(None)

    assert chosen == "srv1.py"


def test_build_client_command_with_device_id():
    module = load_launcher_module()

    cmd = module.build_client_command(
        device_id=3, output_dir="outdir", webui_url="http://x"
    )

    assert "--device-id" in cmd and "3" in cmd
    assert "--output-dir" in cmd and "outdir" in cmd
    assert "--webui-url" in cmd and "http://x" in cmd


def test_build_server_command_with_data_dir():
    module = load_launcher_module()

    cmd = module.build_server_command("srv.py", data_dir="/tmp/data")

    assert cmd[:2] == [module.sys.executable, "srv.py"]
    assert "--data-dir" in cmd and "/tmp/data" in cmd


def test_prompt_output_dir_default(monkeypatch):
    module = load_launcher_module()
    monkeypatch.setattr("builtins.input", lambda _: "")

    result = module.prompt_output_dir(default="rec")

    assert result == "rec"
