from pathlib import Path

from click.testing import CliRunner

from architecture_diagrams.archdiags import cli


def test_generate_smoke_tmp(tmp_path: Path):
    out = tmp_path / "smoke.dsl"
    runner = CliRunner()
    res = runner.invoke(cli, ["generate", "--project", "banking", "--output", str(out)])
    assert res.exit_code == 0, res.output
    assert out.exists()
    text = out.read_text()
    assert "workspace {" in text
