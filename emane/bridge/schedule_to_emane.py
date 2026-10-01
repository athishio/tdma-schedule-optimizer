"""
EMANE TDMA Schedule Generator and Validator.

Reads schedule JSON produced by the TDMA Optimizer (Part 1) and generates:
1. EMANE TDMA Event Schedule XML configuration for the tdmaeventschedulerradiomodel.
2. Standalone Python EMANE Event publishing script using emane.events bindings.
3. Round-trip validation to verify exact consistency without requiring EMANE.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Set, Tuple


def node_name_to_nem_id(node_name: str) -> int:
    """
    Extract integer NEM ID from node name (e.g. 'Node_01' -> 1, 'Node_16' -> 16).
    Falls back to deterministic hash if no integer is found.
    """
    match = re.search(r"(\d+)$", node_name)
    if match:
        return int(match.group(1))
    # Fallback: extract any digits
    digits = re.findall(r"\d+", node_name)
    if digits:
        return int(digits[0])
    return (abs(hash(node_name)) % 1000) + 1


def generate_emane_tdma_xml(
    schedule_data: Dict[str, Any],
    slot_duration_us: int = 1000,
    guard_interval_us: int = 50,
    frequency_hz: int = 2400000000,
    bandwidth_hz: int = 20000000,
    power_dbm: float = 0.0,
    datarate_bps: int = 10000000,
) -> str:
    """
    Generate the EMANE TDMA Schedule XML for tdmaeventschedulerradiomodel.

    Mapping:
    - Each frame contains K slots (where K is the optimized frame length).
    - Slot duration is specified in microseconds (default 1000 us = 1 ms).
    - In each slot, assigned nodes are configured as Transmitters (TX).
    - All non-assigned nodes operate in Receive (RX) mode on the shared carrier frequency.

    Args:
        schedule_data: Dictionary loaded from Part 1 schedule JSON export.
        slot_duration_us: Slot length in microseconds (default: 1000 us).
        guard_interval_us: Slot guard interval in microseconds (default: 50 us).
        frequency_hz: Radio frequency in Hz (default: 2.4 GHz).
        bandwidth_hz: Channel bandwidth in Hz (default: 20 MHz).
        power_dbm: Transmit power in dBm (default: 0 dBm).
        datarate_bps: Over-the-air data rate in bps (default: 10 Mbps).

    Returns:
        str: Pretty-printed XML schedule string.
    """
    schedule: Dict[str, int] = schedule_data.get("schedule", {})
    if not schedule:
        raise ValueError("Schedule data is empty or missing 'schedule' key.")

    k = max(schedule.values()) + 1
    total_nodes = len(schedule)

    # Group nodes by slot
    slot_to_nodes: Dict[int, List[str]] = {slot_idx: [] for slot_idx in range(k)}
    for node, slot in schedule.items():
        slot_to_nodes[slot].append(node)

    root = ET.Element("emane-tdma-schedule")

    # 1. Structure definition
    structure = ET.SubElement(
        root,
        "structure",
        {
            "frames": "1",
            "slots": str(k),
            "slotduration": str(slot_duration_us),
            "guardtime": str(guard_interval_us),
        },
    )

    # 2. Multiframe definition
    multiframe = ET.SubElement(root, "multiframe")
    frame = ET.SubElement(multiframe, "frame", {"index": "0"})

    all_nems: Set[int] = {node_name_to_nem_id(n) for n in schedule.keys()}

    for slot_idx in range(k):
        assigned_nodes = slot_to_nodes[slot_idx]
        tx_nems = sorted([node_name_to_nem_id(n) for n in assigned_nodes])
        tx_str = ",".join(str(nem) for nem in tx_nems) if tx_nems else "none"

        # RX NEMs are all nodes not transmitting in this slot
        rx_nems = sorted(list(all_nems - set(tx_nems)))
        rx_str = ",".join(str(nem) for nem in rx_nems) if rx_nems else "*"

        slot_elem = ET.SubElement(
            frame,
            "slot",
            {
                "index": str(slot_idx),
                "nodes": tx_str,
                "tx": tx_str,
                "rx": rx_str,
                "frequency": str(frequency_hz),
                "bandwidth": str(bandwidth_hz),
                "power": f"{power_dbm:.1f}",
                "datarate": str(datarate_bps),
            },
        )

    # Format with indentation
    ET.indent(root, space="  ")
    xml_header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    return xml_header + ET.tostring(root, encoding="unicode") + "\n"


def parse_emane_tdma_xml(xml_content: str) -> Dict[str, Any]:
    """
    Parse an EMANE TDMA schedule XML document back into structured format.
    Used for round-trip validation without needing EMANE installed.
    """
    root = ET.fromstring(xml_content)

    structure = root.find("structure")
    if structure is None:
        raise ValueError("Missing <structure> element in EMANE schedule XML")

    slots_count = int(structure.attrib["slots"])
    slot_duration = int(structure.attrib["slotduration"])

    frame = root.find(".//frame")
    if frame is None:
        raise ValueError("Missing <frame> element in EMANE schedule XML")

    slot_assignments: Dict[int, List[int]] = {}
    for slot_elem in frame.findall("slot"):
        slot_idx = int(slot_elem.attrib["index"])
        nodes_attr = slot_elem.attrib.get("nodes", "")
        if nodes_attr and nodes_attr != "none":
            nem_ids = [int(x.strip()) for x in nodes_attr.split(",") if x.strip()]
        else:
            nem_ids = []
        slot_assignments[slot_idx] = nem_ids

    return {
        "slots_count": slots_count,
        "slot_duration_us": slot_duration,
        "slot_assignments": slot_assignments,
    }


def validate_round_trip(
    original_schedule_data: Dict[str, Any], xml_content: str
) -> Tuple[bool, List[str]]:
    """
    Validate that the generated EMANE XML schedule exactly matches
    the original optimization schedule matrix.

    Returns:
        Tuple[bool, List[str]]: (is_consistent, error_messages)
    """
    errors: List[str] = []
    parsed = parse_emane_tdma_xml(xml_content)

    orig_schedule: Dict[str, int] = original_schedule_data.get("schedule", {})
    expected_k = max(orig_schedule.values()) + 1

    if parsed["slots_count"] != expected_k:
        errors.append(
            f"Frame length mismatch: XML has {parsed['slots_count']} slots, "
            f"expected {expected_k}"
        )

    # Check each node assignment
    for node, expected_slot in orig_schedule.items():
        nem_id = node_name_to_nem_id(node)
        actual_nems_in_slot = parsed["slot_assignments"].get(expected_slot, [])
        if nem_id not in actual_nems_in_slot:
            errors.append(
                f"Node '{node}' (NEM {nem_id}) missing from Slot {expected_slot} in XML! "
                f"Found NEMs: {actual_nems_in_slot}"
            )

    return (len(errors) == 0), errors


def generate_emane_python_event_script(
    schedule_data: Dict[str, Any],
    output_py_path: str,
    device: str = "eth0",
    group: str = "224.1.2.8:45703",
) -> None:
    """
    Generate a standalone Python script to publish the TDMA schedule
    dynamically using official emane.events bindings.
    """
    schedule = schedule_data.get("schedule", {})
    k = max(schedule.values()) + 1 if schedule else 0

    script_content = f'''#!/usr/bin/env python3
"""
EMANE TDMA Dynamic Schedule Event Publisher.
Generated automatically by TDMA Schedule Optimizer Bridge.

Injects the optimized TDMA schedule into a live EMANE emulation instance
via the EMANE Event Service multicast channel.
"""

import sys
import time

try:
    from emane.events import EventService
    from emane.events import TDMAScheduleEvent
except ImportError:
    print("[ERROR] EMANE Python event libraries (emane.events) are not installed.")
    print("Please run this script inside an environment with EMANE installed.")
    sys.exit(1)


def publish_schedule(event_channel="{group}", device="{device}"):
    """Publish TDMA Schedule Event to active EMANE NEMs."""
    print(f"[INFO] Initializing EMANE EventService on {{device}} ({{event_channel}})...")
    service = EventService(device=device, group=event_channel)

    # Frame structure: 1 frame, {k} slots, 1000 us (1 ms) per slot
    event = TDMAScheduleEvent()
    
    # Slot allocations based on optimized spatial reuse:
'''
    for node, slot in sorted(schedule.items(), key=lambda kv: kv[1]):
        nem_id = node_name_to_nem_id(node)
        script_content += f'    # {node} -> Slot {slot}\n'
        script_content += f'    event.append(nem_id={nem_id}, slot_index={slot}, tx=True)\n'

    script_content += f'''
    print("[INFO] Publishing TDMAScheduleEvent ({k} slots) to all NEMs...")
    service.publish(event)
    print("[SUCCESS] TDMA schedule successfully applied to emulation.")


if __name__ == "__main__":
    publish_schedule()
'''
    with open(output_py_path, "w", encoding="utf-8") as f:
        f.write(script_content)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert TDMA Schedule JSON to EMANE XML configuration and event script"
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to input schedule JSON file exported from TDMA optimizer.",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Path to write EMANE TDMA schedule XML file.",
    )
    parser.add_argument(
        "--event-script",
        "-e",
        help="Optional path to write Python emane.events publisher script.",
    )
    parser.add_argument(
        "--slot-duration-us",
        type=int,
        default=1000,
        help="Slot duration in microseconds (default: 1000 us = 1 ms).",
    )

    args = parser.parse_args(argv)

    if not os.path.exists(args.input):
        print(f"[ERROR] Input schedule file not found: {args.input}", file=sys.stderr)
        return 1

    with open(args.input, "r", encoding="utf-8") as f:
        schedule_data = json.load(f)

    # Generate XML
    xml_output = generate_emane_tdma_xml(
        schedule_data, slot_duration_us=args.slot_duration_us
    )

    # Perform round-trip validation
    is_valid, errors = validate_round_trip(schedule_data, xml_output)
    if not is_valid:
        print("[ERROR] Round-trip validation failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(xml_output)

    print(f"[SUCCESS] EMANE TDMA schedule XML written to: {args.output}")
    print("[INFO] Round-trip verification: schedule matrix matches XML perfectly.")

    if args.event_script:
        generate_emane_python_event_script(schedule_data, args.event_script)
        print(f"[SUCCESS] EMANE Python event script written to: {args.event_script}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
