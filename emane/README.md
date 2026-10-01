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

### Radio Propagation & Range Modeling (Design Only / Untested)
EMANE's TDMA scheduler radio model has no intrinsic knowledge of the discrete 500.0 m communication range constraint. In EMANE, which virtual radios hear each other is determined strictly by node locations and RF pathloss (location/pathloss events) combined with receiver sensitivity and antenna configuration.

To demonstrate spatial reuse in an emulation:
1. **Node Locations & Pathloss:** The emulation must place virtual radios at the exact coordinates defined in the Python topology input using `emane.events.LocationEvent` (Event ID 100) or by publishing explicit pathloss matrices via `emane.events.PathlossEvent` (Event ID 101).
2. **Effective Range Calibration:** The physical layer's transmit power (`txpower = 0.0 dBm`), pathloss model (`propagationmodel = freespace` or `2ray`), and Packet Completion Rate curve (`tdmabasemodelpcr.xml`) must be configured so that the received SINR drops below the decoding threshold at distances exceeding approximately 500.0 meters.
3. **Collision Risk Under Global Visibility:** If the emulation were executed without location/pathloss events or with an uncalibrated propagation model, all 16 virtual radios would hear one another globally across the multicast OTA channel (`224.1.2.8:45703`). Under global visibility, concurrent transmissions scheduled for nodes separated by $\ge 3$ hops (e.g., Node_01 and Node_04 sharing Slot 8 in the 4x4 grid) would collide at the PHY layer, causing packet drops that the graph model proves should not occur.

*Status: DESIGN ONLY / UNTESTED. Offline XML schedule translation and schema parity are fully tested; live RF propagation tuning and packet-level slot enforcement have not been executed on a live Linux kernel testbed.*

---

## 3. EMANE Verification Log

Every element, parameter, and API name has been verified against official documentation, source repositories, or explicitly labeled as an assumption:

| Parameter / Component | Category | Verified Name / Value | Exact Official URL | Quoted Official Documentation | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **MAC Model Library** | MAC Plugin | `tdmaeventschedulerradiomodel` | [tdmaradiomodel.xml.in](https://github.com/adjacentlink/emane/blob/master/src/models/mac/tdma/eventscheduler/tdmaradiomodel.xml.in) | `<mac library='tdmaeventschedulerradiomodel'>` | **VERIFIED** |
| **MAC Parameters vs Structure** | Architecture | Attributes of `<structure>`, not `<mac>` | [tdma-radio-model.txt](https://github.com/adjacentlink/emane-guide/blob/main/guide/tdma-radio-model.txt) | *"The TDMA structure defines: Slot size in microseconds, Slot overhead in microseconds, Number of slots per frame, Number of frames per multiframe, Transceiver bandwidth in Hz"* (lines 160-171) | **VERIFIED** |
| **MAC PCR Curve URI** | MAC Parameter | `pcrcurveuri` | [tdmaradiomodel.xml.in](https://github.com/adjacentlink/emane/blob/master/src/models/mac/tdma/eventscheduler/tdmaradiomodel.xml.in) | `<param name="pcrcurveuri" value='file://@datadir@/xml/models/mac/tdmaeventscheduler/tdmabasemodelpcr.xml'/>` | **VERIFIED** |
| **MAC Queue Controls** | MAC Parameters | `queue.depth`, `queue.aggregationenable`, etc. | [tdmaradiomodel.xml.in](https://github.com/adjacentlink/emane/blob/master/src/models/mac/tdma/eventscheduler/tdmaradiomodel.xml.in) | `<param name='queue.depth' value='255'/><param name='queue.aggregationenable' value='on'/><param name='queue.strictdequeueenable' value='off'/>` | **VERIFIED** |
| **Schedule XML Root** | XML Schema | `<emane-tdma-schedule>` | [tdmaschedule.xsd](https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/schema/tdmaschedule.xsd) | `<xs:element name='emane-tdma-schedule'>` (line 71) | **VERIFIED** |
| **Schedule Structure** | XML Element | `<structure frames='..' slots='..' slotoverhead='..' slotduration='..' bandwidth='..'/>` | [tdmaschedule.xsd](https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/schema/tdmaschedule.xsd) | `<xs:element name="structure" minOccurs='0'><xs:attribute name='slotduration' type='xs:unsignedLong' use='required'/><xs:attribute name='slotoverhead' type='xs:unsignedLong' use='required'/>...` | **VERIFIED** |
| **Multiframe & Frames** | XML Elements | `<multiframe>` containing `<frame index='..'>` | [tdmaschedule.xsd](https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/schema/tdmaschedule.xsd) | `<xs:element name="multiframe"><xs:complexType><xs:sequence><xs:element name="frame" maxOccurs="unbounded">` | **VERIFIED** |
| **Slot Allocation & Types** | XML Elements | `<slot index='..' nodes='..'>` with `<tx>`, `<rx>`, `<idle>` | [tdmaschedule.xsd](https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/schema/tdmaschedule.xsd) | `<xs:element name="slot" maxOccurs="unbounded"><xs:attribute name='index' use='required'/><xs:attribute name='nodes' use='required'/><xs:choice minOccurs='0'><xs:element name="tx">...` | **VERIFIED** |
| **Schedule Injection Tool** | CLI Utility | `emaneevent-tdmaschedule` | [tdma-radio-model.txt](https://github.com/adjacentlink/emane-guide/blob/main/guide/tdma-radio-model.txt) | *"The emaneevent-tdmaschedule script can be used to process a TDMA Schedule XML file... $ emaneevent-tdmaschedule your-desired-schedule.xml -i lo"* (lines 370-377) | **VERIFIED** |
| **Python Event Class** | Python Class | `emane.events.TDMAScheduleEvent` | [tdmascheduleevent.py](https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/tdmascheduleevent.py) | `class TDMAScheduleEvent(Event): IDENTIFIER = 105; def structure(self,**kwargs): ... def append(self,frameIndex,slotIndex,**kwargs):` (lines 38, 86, 163) | **VERIFIED** |
| **Python Event Publisher** | Python Class | `emane.events.EventService` | [eventservice.py](https://github.com/adjacentlink/emane/blob/master/src/python/emane/events/eventservice.py) | `class EventService: def __init__(self,eventchannel,otachannel = None): (self._multicastGroup,self._port,_) = eventchannel; def publish(self,nemId,event):` (lines 127, 345) | **VERIFIED** |

---

## 4. Building and Running the EMANE Environment

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

## 5. End-to-End Workflow: Schedule Optimization to EMANE

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

## 6. Emulation Verification Test Plan

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
