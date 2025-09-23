from pathlib import Path

from click.testing import CliRunner

from architecture_diagrams.cli.generate import generate


def test_cli_generate_fails_for_missing_internal_project(tmp_path: Path):
    out_file = tmp_path / "out.dsl"
    runner = CliRunner()
    result = runner.invoke(
        generate,
        ["--project", "__definitely_missing__", "--output", str(out_file)],
        mix_stderr=True,
    )
    # Expect non-zero exit and no output file created
    assert result.exit_code != 0
    assert not out_file.exists()


def test_cli_generate_fails_for_missing_project_path(tmp_path: Path):
    out_file = tmp_path / "out.dsl"
    bad = tmp_path / "does-not-exist"
    runner = CliRunner()
    result = runner.invoke(
        generate, ["--project-path", str(bad), "--output", str(out_file)], mix_stderr=True
    )
    assert result.exit_code != 0
    assert not out_file.exists()
