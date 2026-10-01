# EMANE Integration Bridge & Emulation Testbed

This directory provides the integration layer between the **TDMA Schedule Optimizer** (Part 1) and the **Extendable Mobile Ad-hoc Network Emulator (EMANE)** framework.

---

## 1. Overview & Architecture

EMANE is a real-time, link-layer and physical-layer wireless emulator developed by Adjacent Link LLC. It enables high-fidelity simulation of over-the-air RF propagation, packet collision, SINR (Signal-to-Interference-plus-Noise Ratio), and channel access scheduling.

```
+-------------------------------------------------------------+
|               TDMA Schedule Optimizer (Part 1)             |
|   Coordinates JSON  -->  Conflict Graph G^2  --> Optimizer  |
+-------------------------------------------------------------+
                              |
                     export schedule.json
                              v
+-------------------------------------------------------------+
|             EMANE Translation Bridge (Part 2)               |
|            emane/bridge/schedule_to_emane.py                |
+-------------------------------------------------------------+
            /                                    \
           v                                      v
  schedule.xml (Static Schedule)     publish_event.py (Dynamic)
  Config for EMANE TDMA MAC          emane.events.TDMAScheduleEvent
           \                                      /
            +-----------------+------------------+
                              v
+-------------------------------------------------------------+
|                EMANE Virtual Emulation Node                 |
|   [Linux Netns/TAP emane0] <-> [TDMA MAC] <-> [PHY/OTA RF]  |
+-------------------------------------------------------------+
```

### Components
1. **`Dockerfile`**: A single consolidated Ubuntu 22.04 container definition installing EMANE, Python event bindings, and network benchmarking utilities (`iproute2`, `iperf3`, `tcpdump`, `ping`).
2. **`config/`**: Native XML configuration profiles for EMANE's `tdmaeventschedulerradiomodel`:
   - `mac-tdmaeventschedule.xml`: MAC configuration enforcing 1.0 ms slots (`slotduration="1000"` usec), 50 usec guard time, and queue parameters.
   - `phy-universal.xml`: Physical layer on 2.4 GHz (`2400000000` Hz), 20 MHz bandwidth, 0 dBm transmit power, and free-space path loss.
   - `nem.xml`: Network Emulation Module binding Transport $\rightarrow$ MAC $\rightarrow$ PHY.
   - `transportdaemon.xml`: Virtual TAP interface driver mapping host IP sockets to the TDMA MAC.
   - `platform.xml`: Platform definition instantiating 16 NEMs (nodes 1–16) on a virtual multicast OTA channel.
3. **`bridge/schedule_to_emane.py`**: Automated schedule translator that parses optimization results from Part 1, maps each node to its transmission slot (Tx) and non-transmitting slots to receive (Rx), and generates valid schedule XML and Python event scripts.

---

## 2. Tested vs. Design-Only Boundary

To maintain complete transparency and integrity:

| Subsystem / Feature | Status | Verification Methodology |
| :--- | :--- | :--- |
| **Schedule Parsing & NEM ID Mapping** | **Tested** | Unit tested via pytest on multiple topologies (`Node_01` $\rightarrow$ NEM 1). |
| **EMANE Schedule XML Generation** | **Tested** | Round-trip XML parsing and structural schema verification without requiring EMANE. |
| **Schedule-to-Matrix Round-Trip Parity** | **Tested** | Asserted that every node's assigned slot in the XML matches the optimization matrix. |
| **Python Event Script Generation** | **Tested** | Script generation syntax and parameter formatting tested. |
| **EMANE Emulation Runtime (Over-The-Air)** | **Design Only** | Documented test plan below; requires Linux kernel TAP/TUN, root privileges, and EMANE daemon execution. |

---

## 3. Building and Running the EMANE Environment

### Option A: Official Binary Installation (Host Linux)
On Ubuntu/Debian systems, install via the official Adjacent Link community package repositories:
```bash
sudo add-apt-repository ppa:adjacentlink/community
sudo apt-get update
sudo apt-get install emane emane-model-tdma python3-emane
```

### Option B: Docker Container
Build the standalone container provided in `emane/Dockerfile`:
```bash
# Build the container image
docker build -t tdma-emane:latest -f emane/Dockerfile .

# Run with privileged network capabilities (required for TUN/TAP devices)
docker run -it --rm --cap-add=NET_ADMIN --device /dev/net/tun tdma-emane:latest
```

---

## 4. End-to-End Workflow: Schedule Optimization to EMANE

### Step 1: Optimize Schedule and Export JSON
Run the optimizer on the 4x4 grid topology:
```bash
python -m tdma.cli \
  --coords-file examples/grid_4x4_300m.json \
  --export-json examples/grid_schedule.json
```

### Step 2: Convert to EMANE TDMA Schedule
Convert the JSON schedule into EMANE XML configuration:
```bash
python emane/bridge/schedule_to_emane.py \
  --input examples/grid_schedule.json \
  --output emane/config/schedule.xml \
  --event-script emane/bridge/publish_schedule.py \
  --slot-duration-us 1000
```
This produces:
- `emane/config/schedule.xml`: Valid schedule XML with 1 ms slots and assigned TX/RX nodes.
- `emane/bridge/publish_schedule.py`: Python event publisher.

---

## 5. Emulation Verification Test Plan

The following test plan demonstrates TDMA slot enforcement and collision avoidance in a running EMANE deployment:

### Test Case 1: Slot Enforcement (Valid Schedule)
* **Objective**: Confirm that packets traverse the radio link only during the transmitter's assigned TDMA slot.
* **Procedure**:
  1. Launch the 16-node EMANE platform with the optimized schedule (`emane platform.xml`).
  2. Start `tcpdump` with microsecond timestamp resolution on Node 2 (`emane0`):
     ```bash
     tcpdump -i emane0 -tttt -nn -xx "icmp"
     ```
  3. Send 10 ICMP ping packets from Node 1 to Node 2:
     ```bash
     ping -c 10 -i 0.1 10.0.0.2
     ```
* **Expected Outcome**:
  - All 10 pings succeed with 0% packet loss.
  - Inter-packet arrival intervals align with multiples of the frame duration ($9 \times 1\text{ ms} = 9\text{ ms}$).
  - Packets are emitted exclusively in Node 1's designated time slot (Slot 8 in the grid schedule).

### Test Case 2: Intentional Collision Demonstration (Conflicting Schedule)
* **Objective**: Prove that violating distance-1 or distance-2 constraints causes RF interference and frame drops.
* **Procedure**:
  1. Generate a deliberately corrupted schedule where adjacent nodes (Node 1 and Node 2) are both forced into Slot 0.
  2. Inject the corrupted schedule using the event service:
     ```bash
     emaneevent-tdmaschedule -i eth0 emane/config/corrupted_schedule.xml
     ```
  3. Concurrently transmit high-rate UDP streams from Node 1 and Node 2 to Node 6:
     ```bash
     # From Node 1:
     iperf3 -u -c 10.0.0.6 -b 5M -t 5
     # Concurrently from Node 2:
     iperf3 -u -c 10.0.0.6 -b 5M -t 5
     ```
* **Expected Outcome**:
  - The EMANE Universal PHY model detects overlapping RF power from NEM 1 and NEM 2 during Slot 0.
  - The Signal-to-Interference-plus-Noise Ratio (SINR) drops below the Packet Clear Rate (PCR) threshold.
  - EMANE increments the PHY discard counter (`numRxDropInterference`), resulting in heavy packet loss (> 80%) at Node 6.
