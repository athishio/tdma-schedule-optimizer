"""
Unit and integration tests for EMANE TDMA bridge.
Tests can run in any environment without requiring EMANE installed.
"""

import json
import os
import tempfile
import pytest

from emane.bridge.schedule_to_emane import (
    node_name_to_nem_id,
    generate_emane_tdma_xml,
    parse_emane_tdma_xml,
    validate_round_trip,
    generate_emane_python_event_script,
    main,
)


def test_node_name_to_nem_id():
    assert node_name_to_nem_id("Node_01") == 1
    assert node_name_to_nem_id("Node_16") == 16
    assert node_name_to_nem_id("N42") == 42
    assert node_name_to_nem_id("ClusterB_08") == 8


def test_round_trip_grid_schedule():
    sample_data = {
        "schedule": {
            "Node_01": 0,
            "Node_02": 1,
            "Node_03": 2,
            "Node_04": 0,  # Spatial reuse
            "Node_05": 1,
            "Node_06": 2,
        }
    }
    xml_str = generate_emane_tdma_xml(sample_data, slot_duration_us=1000)
    assert 'frames="1"' in xml_str
    assert 'slots="3"' in xml_str
    assert 'slotduration="1000"' in xml_str
    assert 'nodes="1,4"' in xml_str

    parsed = parse_emane_tdma_xml(xml_str)
    assert parsed["slots_count"] == 3
    assert parsed["slot_duration_us"] == 1000
    assert 1 in parsed["slot_assignments"][0]
    assert 4 in parsed["slot_assignments"][0]

    is_valid, errors = validate_round_trip(sample_data, xml_str)
    assert is_valid
    assert len(errors) == 0


def test_emane_bridge_cli(tmp_path):
    sample_data = {
        "schedule": {
            "Node_01": 0,
            "Node_02": 1,
            "Node_03": 0,
        }
    }
    input_json = tmp_path / "sched.json"
    output_xml = tmp_path / "sched.xml"
    output_py = tmp_path / "pub.py"

    input_json.write_text(json.dumps(sample_data), encoding="utf-8")

    exit_code = main(
        [
            "--input",
            str(input_json),
            "--output",
            str(output_xml),
            "--event-script",
            str(output_py),
        ]
    )

    assert exit_code == 0
    assert output_xml.exists()
    assert output_py.exists()

    xml_text = output_xml.read_text(encoding="utf-8")
    assert "<emane-tdma-schedule>" in xml_text
    py_text = output_py.read_text(encoding="utf-8")
    assert "TDMAScheduleEvent" in py_text
