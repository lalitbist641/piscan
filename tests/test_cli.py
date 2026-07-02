from typer.testing import CliRunner
from piscan.cli import app

runner = CliRunner()

def test_info():
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0

def test_payloads():
    result = runner.invoke(app, ["payloads"])
    assert result.exit_code == 0

def test_benign():
    result = runner.invoke(app, ["benign"])
    assert result.exit_code == 0