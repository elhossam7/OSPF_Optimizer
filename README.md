# OSPF Optimizer - Dynamic OSPF Cost Adjustment

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FRRouting](https://img.shields.io/badge/FRRouting-latest-orange.svg)](https://frrouting.org/)

## Overview

OSPF Optimizer is an intelligent network optimization tool that dynamically adjusts OSPF costs in **FRRouting** networks based on real-time performance metrics:

- **Bandwidth Utilization** - Monitors link capacity usage
- **Latency** - Tracks network delay patterns
- **Packet Loss** - Detects and responds to quality degradation

## Architecture

| Component | Technology |
|-----------|-------------|
| Routing Engine | **FRRouting (FRR)** - Docker Containers |
| End Devices | **Alpine Linux** - Docker Containers |
| Network Simulator | **GNS3** |
| Management | Direct Docker Exec (SSH-free) |

## Prerequisites

- Python 3.8 or higher
- Docker Engine
- GNS3 (for network simulation)
- FRRouting containers

## Installation

```bash
cd ~/OSPF_Optimizer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Quick Start

### Automatic Deployment (Recommended)

The `auto_start.py` script automatically detects GNS3 containers and configures the environment:

```bash
# Standard deployment with web dashboard
python3 auto_start.py --web

# Test mode (dry-run) with verbose output
python3 auto_start.py --dry-run --verbose

# Container detection only
python3 auto_start.py --detect-only
```

**Alternative Shell Script (Linux/Unix):**
```bash
chmod +x auto_start.sh
./auto_start.sh --web --port 8080
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--web` | Enable web-based dashboard |
| `--port <PORT>` | Web server port (default: 8080) |
| `--dry-run` | Preview changes without applying |
| `--verbose` | Enable detailed logging |
| `--detect-only` | Detect containers without starting services |
| `--no-update` | Use existing configuration |
| `--simulation` | Run with simulated metrics |
| `--once` | Execute single optimization cycle and exit |

## Manual Operation

### Simulation Mode

Test the optimizer with simulated network data:

```bash
python3 ospf_optimizer.py --simulation --once
```

### Production Mode

Run against live network infrastructure:

```bash
python3 ospf_optimizer.py --once
```

### Web Dashboard

Launch the monitoring dashboard:

```bash
python3 ospf_optimizer.py --config config/routers.yaml --web --port 8080
```

## FRRouting Commands

### Verify OSPF Neighbors
```bash
docker exec R1 vtysh -c "show ip ospf neighbor"
```

### Check OSPF Interfaces
```bash
docker exec R1 vtysh -c "show ip ospf interface"
```

### Display OSPF Routes
```bash
docker exec R1 vtysh -c "show ip route ospf"
```

## Configuration

Configuration files are located in `config/routers.yaml`. See [Configuration Guide](docs/configuration.md) for details.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## Support

For issues and questions, please open an issue on the GitHub repository.

