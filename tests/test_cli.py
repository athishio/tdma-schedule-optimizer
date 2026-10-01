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


def test_matrix_header_unique_labels_for_shared_suffixes(capsys):
    """Verify that matrix headers do not produce duplicate stripped column labels."""
    from tdma.report import format_report, format_comparison_table

    # Case 1: Shared numeric suffixes across different prefixes
    sched_shared = {
        "ClusterA_01": 0,
        "ClusterA_02": 1,
        "ClusterB_01": 0,
        "ClusterB_02": 1,
    }
    coords_shared = {k: [0.0, 0.0] for k in sched_shared}
    report_shared = format_report(coords_shared, sched_shared, 500.0, True)

    # Extract header line
    lines = report_shared.splitlines()
    header_idx = [i for i, line in enumerate(lines) if "Slot \\ Node |" in line][0]
    header_line = lines[header_idx]
    col_labels = [c.strip() for c in header_line.split("|")[1:]]

    # Must be 4 unique column headers, not ['01', '02', '01', '02']
    assert len(col_labels) == 4
    assert len(set(col_labels)) == 4
    assert "ClusterA_01" in col_labels
    assert "ClusterB_01" in col_labels

    # Case 2: Node_XX keeps the compact 01 | 02 format
    sched_nodes = {
        "Node_01": 0,
        "Node_02": 1,
    }
    coords_nodes = {k: [0.0, 0.0] for k in sched_nodes}
    report_nodes = format_report(coords_nodes, sched_nodes, 500.0, True)
    lines_nodes = report_nodes.splitlines()
    h_idx_nodes = [i for i, line in enumerate(lines_nodes) if "Slot \\ Node |" in line][0]
    col_labels_nodes = [c.strip() for c in lines_nodes[h_idx_nodes].split("|")[1:]]
    assert col_labels_nodes == ["01", "02"]


def test_fallback_solver_label_shortened_with_footnote():
    """Verify fallback solver label is shortened to Exact (Python B&B) with footnote."""
    from tdma.report import format_comparison_table

    heuristic_results = {
        "DSATUR": {"slots_used": 8, "runtime_ms": 0.12},
    }
    table = format_comparison_table(
        heuristic_results,
        optimum=8,
        exact_solver_name="Pure-Python Branch-and-Bound (DSATUR)",
        exact_runtime_ms=0.45,
    )
    assert "Exact (Python B&B)" in table
    assert "* Exact (Python B&B): Pure-Python Branch-and-Bound (DSATUR)" in table

