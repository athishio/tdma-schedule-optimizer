#!/usr/bin/env python3
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


def publish_schedule(group="224.1.2.8", port=45703, device="eth0"):
    """Publish TDMA Schedule Event to active EMANE NEMs using official EventService."""
    print(f"[INFO] Initializing EMANE EventService on {device} ({group}:{port})...")
    service = EventService(eventchannel=(group, int(port), device))

    # Construct full schedule definition
    event = TDMAScheduleEvent(frequency=2400000000, datarate=10000000, service=0, power=0.0)
    event.structure(
        slots=9,
        frames=1,
        slotduration=1000,
        slotoverhead=50,
        bandwidth=20000000
    )

    # Per-NEM schedule allocations:
    event.append(0, 8, type="tx")  # NEM 1 transmits in Frame 0, Slot 8
    service.publish(1, event)
    event.append(0, 4, type="tx")  # NEM 2 transmits in Frame 0, Slot 4
    service.publish(2, event)
    event.append(0, 5, type="tx")  # NEM 3 transmits in Frame 0, Slot 5
    service.publish(3, event)
    event.append(0, 8, type="tx")  # NEM 4 transmits in Frame 0, Slot 8
    service.publish(4, event)
    event.append(0, 6, type="tx")  # NEM 5 transmits in Frame 0, Slot 6
    service.publish(5, event)
    event.append(0, 0, type="tx")  # NEM 6 transmits in Frame 0, Slot 0
    service.publish(6, event)
    event.append(0, 1, type="tx")  # NEM 7 transmits in Frame 0, Slot 1
    service.publish(7, event)
    event.append(0, 6, type="tx")  # NEM 8 transmits in Frame 0, Slot 6
    service.publish(8, event)
    event.append(0, 7, type="tx")  # NEM 9 transmits in Frame 0, Slot 7
    service.publish(9, event)
    event.append(0, 2, type="tx")  # NEM 10 transmits in Frame 0, Slot 2
    service.publish(10, event)
    event.append(0, 3, type="tx")  # NEM 11 transmits in Frame 0, Slot 3
    service.publish(11, event)
    event.append(0, 7, type="tx")  # NEM 12 transmits in Frame 0, Slot 7
    service.publish(12, event)
    event.append(0, 8, type="tx")  # NEM 13 transmits in Frame 0, Slot 8
    service.publish(13, event)
    event.append(0, 4, type="tx")  # NEM 14 transmits in Frame 0, Slot 4
    service.publish(14, event)
    event.append(0, 5, type="tx")  # NEM 15 transmits in Frame 0, Slot 5
    service.publish(15, event)
    event.append(0, 8, type="tx")  # NEM 16 transmits in Frame 0, Slot 8
    service.publish(16, event)

    print("[SUCCESS] TDMA schedule (9 slots) successfully published to all NEMs.")


if __name__ == "__main__":
    publish_schedule()
