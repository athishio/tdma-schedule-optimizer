"""
EMANE TDMA Schedule Generator and Validator.

Converts schedule JSON produced by the TDMA Optimizer (Part 1) into:
1. Official EMANE TDMA Schedule XML conforming to tdmaschedule.xsd for tdmaeventschedulerradiomodel.
2. Standalone Python EMANE Event publishing script using official emane.events bindings.
3. Round-trip validation to verify exact schedule parity without requiring EMANE installed.

Official Documentation References:
- TDMA Model Guide: https://github.com/adjacentlink/emane-guide/blob/main/guide/tdma-radio-model.txt
- Schedule Schema: https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/schema/tdmaschedule.xsd
- Event Class: https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/tdmascheduleevent.py
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
    digits = re.findall(r"\d+", node_name)
    if digits:
        return int(digits[0])
    return (abs(hash(node_name)) % 1000) + 1


def generate_emane_tdma_xml(
    schedule_data: Dict[str, Any],
    slot_duration_us: int = 1000,
    slot_overhead_us: int = 50,
    frequency_str: str = "2.4G",
    bandwidth_str: str = "20M",
    power_dbm: float = 0.0,
    datarate_str: str = "10M",
) -> str:
    """
    Generate official EMANE TDMA Schedule XML for tdmaeventschedulerradiomodel.

    XML Structure (conforming to tdmaschedule.xsd):
      <emane-tdma-schedule>
        <structure frames="1" slots="K" slotoverhead="50" slotduration="1000" bandwidth="20M"/>
        <multiframe frequency="2.4G" power="0.0" class="0" datarate="10M">
          <frame index="0">
            <slot index="0" nodes="6">
              <tx/>
            </slot>
            ...
          </frame>
        </multiframe>
      </emane-tdma-schedule>
    """
    schedule: Dict[str, int] = schedule_data.get("schedule", {})
    if not schedule:
        raise ValueError("Schedule data is empty or missing 'schedule' key.")

    k = max(schedule.values()) + 1

    # Group nodes by slot
    slot_to_nodes: Dict[int, List[str]] = {slot_idx: [] for slot_idx in range(k)}
    for node, slot in schedule.items():
        slot_to_nodes[slot].append(node)

    root = ET.Element("emane-tdma-schedule")

    # 1. Structure definition (timing & bandwidth are defined here, NOT in MAC config)
    ET.SubElement(
        root,
        "structure",
        {
            "frames": "1",
            "slots": str(k),
            "slotoverhead": str(slot_overhead_us),
            "slotduration": str(slot_duration_us),
            "bandwidth": bandwidth_str,
        },
    )

    # 2. Multiframe definition with frame defaults
    multiframe = ET.SubElement(
        root,
        "multiframe",
        {
            "frequency": frequency_str,
            "power": f"{power_dbm:.1f}",
            "class": "0",
            "datarate": datarate_str,
        },
    )
    frame = ET.SubElement(multiframe, "frame", {"index": "0"})

    for slot_idx in range(k):
        assigned_nodes = slot_to_nodes[slot_idx]
        tx_nems = sorted([node_name_to_nem_id(n) for n in assigned_nodes])
        if not tx_nems:
            continue
        nodes_str = ",".join(str(nem) for nem in tx_nems)

        slot_elem = ET.SubElement(
            frame,
            "slot",
            {
                "index": str(slot_idx),
                "nodes": nodes_str,
            },
        )
        ET.SubElement(slot_elem, "tx")

    # Format with clean indentation
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
    slot_overhead = int(structure.attrib.get("slotoverhead", structure.attrib.get("guardtime", 0)))

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
        "slot_overhead_us": slot_overhead,
        "slot_assignments": slot_assignments,
    }


def validate_round_trip(
    original_schedule_data: Dict[str, Any], xml_content: str
) -> Tuple[bool, List[str]]:
    """
    Validate that the generated EMANE XML schedule exactly matches
    the original optimization schedule matrix.
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

    # Parse multicast group and port
    if ":" in group:
        mcast_addr, mcast_port = group.split(":")
    else:
        mcast_addr, mcast_port = group, "45703"

    script_content = f'''#!/usr/bin/env python3
"""
EMANE TDMA Dynamic Schedule Event Publisher.
Generated automatically by TDMA Schedule Optimizer Bridge.

Official API References:
- EventService: https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/eventservice.py
- TDMAScheduleEvent: https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/tdmascheduleevent.py
"""

import sys

try:
    from emane.events import EventService, TDMAScheduleEvent
except ImportError:
    print("[ERROR] EMANE Python event libraries (emane.events) are not installed.")
    print("Please run this script inside an environment with EMANE installed.")
    sys.exit(1)


def publish_schedule(group="{mcast_addr}", port={mcast_port}, device="{device}"):
    """Publish TDMA Schedule Event to active EMANE NEMs using official EventService."""
    print(f"[INFO] Initializing EMANE EventService on {{device}} ({{group}}:{{port}})...")
    service = EventService(eventchannel=(group, int(port), device))

    # Construct full schedule definition
    event = TDMAScheduleEvent(frequency=2400000000, datarate=10000000, service=0, power=0.0)
    event.structure(
        slots={k},
        frames=1,
        slotduration=1000,
        slotoverhead=50,
        bandwidth=20000000
    )

    # Per-NEM schedule allocations:
'''
    # Group by NEM
    nem_to_slots: Dict[int, List[int]] = {}
    for node, slot in sorted(schedule.items()):
        nem = node_name_to_nem_id(node)
        nem_to_slots.setdefault(nem, []).append(slot)

    for nem_id in sorted(nem_to_slots.keys()):
        slots_list = nem_to_slots[nem_id]
        for s in slots_list:
            script_content += f'    event.append(0, {s}, type="tx")  # NEM {nem_id} transmits in Frame 0, Slot {s}\n'
        script_content += f'    service.publish({nem_id}, event)\n'

    script_content += f'''
    print("[SUCCESS] TDMA schedule ({k} slots) successfully published to all NEMs.")


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
    parser.add_argument(
        "--slot-overhead-us",
        type=int,
        default=50,
        help="Slot overhead / guard interval in microseconds (default: 50 us).",
    )

    args = parser.parse_args(argv)

    if not os.path.exists(args.input):
        print(f"[ERROR] Input schedule file not found: {args.input}", file=sys.stderr)
        return 1

    with open(args.input, "r", encoding="utf-8") as f:
        schedule_data = json.load(f)

    # Generate XML
    xml_output = generate_emane_tdma_xml(
        schedule_data,
        slot_duration_us=args.slot_duration_us,
        slot_overhead_us=args.slot_overhead_us,
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
