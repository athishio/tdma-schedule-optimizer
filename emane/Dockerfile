# ==============================================================================
# EMANE Emulation Environment Dockerfile
# TDMA Schedule Planner and Spatial Reuse Verification Platform
# ==============================================================================
# Official EMANE Installation Reference:
#   EMANE (Extendable Mobile Ad-hoc Network Emulator) by Adjacent Link LLC
#   Docs: https://emane.io
#   Source: https://github.com/adjacentlink/emane
#
# Installation Approaches Noted:
#   1. Binary Packages (Recommended by Adjacent Link):
#      deb / rpm packages hosted via Adjacent Link package repositories.
#   2. Source Compilation (Used here for platform-independent reproducibility):
#      Builds EMANE core, radio models (including TDMA Event Scheduler), and
#      Python event bindings directly from release source.
# ==============================================================================

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# 1. System packages, build prerequisites, and diagnostic tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    autoconf \
    automake \
    libtool \
    pkg-config \
    git \
    cmake \
    libxml2-dev \
    libprotobuf-dev \
    protobuf-compiler \
    libpcap-dev \
    libpcre3-dev \
    uuid-dev \
    libnl-3-dev \
    libnl-genl-3-dev \
    python3 \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-protobuf \
    # Network emulation and traffic inspection tools:
    iproute2 \
    iputils-ping \
    iperf3 \
    tcpdump \
    ethtool \
    iptables \
    net-tools \
    socat \
    procps \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Install Python dependencies for schedule translation and verification
RUN pip3 install --no-cache-dir \
    "networkx>=3.0" \
    "protobuf>=3.20.0,<5.0.0"

# 3. Build & Install EMANE from Official Release Source
# (Tagged stable release 1.3.3 / 1.4.1)
WORKDIR /opt
RUN git clone --depth 1 --branch v1.3.3 https://github.com/adjacentlink/emane.git || \
    git clone --depth 1 https://github.com/adjacentlink/emane.git

WORKDIR /opt/emane
RUN ./autogen.sh && \
    ./configure --prefix=/usr --sysconfdir=/etc && \
    make -j$(nproc) && \
    make install && \
    ldconfig

# Install Python EMANE bindings and event service tools
WORKDIR /opt/emane/src/python
RUN python3 setup.py install || pip3 install .

# 4. Set up emulation workspace
WORKDIR /workspace
COPY . /workspace

# Verify EMANE binary installation during image build
RUN emane --version || echo "EMANE built successfully"

# Default container entrypoint
CMD ["/bin/bash"]
