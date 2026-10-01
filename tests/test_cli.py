"""
End-to-end and CLI tests for TDMA schedule optimizer.
"""

import json
import os
import subprocess
import sys
import tempfile
import pytest

from tdma.cli import main


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "TDMA Schedule Planner" in captured.out


def test_cli_with_inline_coords(capsys):
    raw = '{"N1": [0.0, 0.0], "N2": [350.0, 0.0], "N3": [700.0, 0.0]}'
    exit_code = main(["--coords", raw, "--compare"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "TDMA TOPOLOGY OPTIMIZATION REPORT" in captured.out
    assert "Schedule verified conflict-free." in captured.out
    assert "Optimized Frame Length : 3 unique timeslots" in captured.out


def test_cli_with_coords_file(tmp_path, capsys):
    data = {"Node_A": [0, 0], "Node_B": [100, 100]}
    fpath = tmp_path / "topo.json"
    fpath.write_text(json.dumps(data), encoding="utf-8")

    exit_code = main(["--coords-file", str(fpath)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Total Nodes Processed : 2" in captured.out
    assert "Schedule verified conflict-free." in captured.out


def test_cli_with_json_export_and_plot(tmp_path, capsys):
    data = {"N1": [0, 0], "N2": [300, 0], "N3": [600, 0]}
    coords_file = tmp_path / "nodes.json"
    coords_file.write_text(json.dumps(data), encoding="utf-8")

    export_json = tmp_path / "export.json"
    plot_png = tmp_path / "topology.png"

    exit_code = main(
        [
            "--coords-file",
            str(coords_file),
            "--export-json",
            str(export_json),
            "--plot",
            str(plot_png),
        ]
    )
    assert exit_code == 0
    assert export_json.exists()
    assert plot_png.exists()

    with open(export_json, "r", encoding="utf-8") as f:
        export_data = json.load(f)
    assert "schedule" in export_data
    assert "schedule_matrix" in export_data
    assert export_data["metadata"]["total_nodes"] == 3


def test_cli_malformed_json_exits_nonzero(capsys):
    exit_code = main(["--coords", "{invalid json}"])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "[ERROR] Invalid coordinate input" in captured.err


def test_cli_duplicate_coords_exits_nonzero(capsys):
    raw = '{"Node1": [100.0, 100.0], "Node2": [100.0, 100.0]}'
    exit_code = main(["--coords", raw])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Duplicate coordinates detected" in captured.err


def test_cli_nonexistent_file_exits_nonzero(capsys):
    exit_code = main(["--coords-file", "nonexistent_file_12345.json"])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "Coordinates file not found" in captured.err
