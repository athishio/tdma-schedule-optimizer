#!/usr/bin/env python3
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


def publish_schedule(event_channel="224.1.2.8:45703", device="eth0"):
    """Publish TDMA Schedule Event to active EMANE NEMs."""
    print(f"[INFO] Initializing EMANE EventService on {device} ({event_channel})...")
    service = EventService(device=device, group=event_channel)

    # Frame structure: 1 frame, 9 slots, 1000 us (1 ms) per slot
    event = TDMAScheduleEvent()
    
    # Slot allocations based on optimized spatial reuse:
    # Node_06 -> Slot 0
    event.append(nem_id=6, slot_index=0, tx=True)
    # Node_07 -> Slot 1
    event.append(nem_id=7, slot_index=1, tx=True)
    # Node_10 -> Slot 2
    event.append(nem_id=10, slot_index=2, tx=True)
    # Node_11 -> Slot 3
    event.append(nem_id=11, slot_index=3, tx=True)
    # Node_02 -> Slot 4
    event.append(nem_id=2, slot_index=4, tx=True)
    # Node_14 -> Slot 4
    event.append(nem_id=14, slot_index=4, tx=True)
    # Node_03 -> Slot 5
    event.append(nem_id=3, slot_index=5, tx=True)
    # Node_15 -> Slot 5
    event.append(nem_id=15, slot_index=5, tx=True)
    # Node_05 -> Slot 6
    event.append(nem_id=5, slot_index=6, tx=True)
    # Node_08 -> Slot 6
    event.append(nem_id=8, slot_index=6, tx=True)
    # Node_09 -> Slot 7
    event.append(nem_id=9, slot_index=7, tx=True)
    # Node_12 -> Slot 7
    event.append(nem_id=12, slot_index=7, tx=True)
    # Node_01 -> Slot 8
    event.append(nem_id=1, slot_index=8, tx=True)
    # Node_04 -> Slot 8
    event.append(nem_id=4, slot_index=8, tx=True)
    # Node_13 -> Slot 8
    event.append(nem_id=13, slot_index=8, tx=True)
    # Node_16 -> Slot 8
    event.append(nem_id=16, slot_index=8, tx=True)

    print("[INFO] Publishing TDMAScheduleEvent (9 slots) to all NEMs...")
    service.publish(event)
    print("[SUCCESS] TDMA schedule successfully applied to emulation.")


if __name__ == "__main__":
    publish_schedule()
