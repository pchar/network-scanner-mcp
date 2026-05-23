# Project Summary

## Overall Goal
Inspection and analysis of the `network-scanner-mcp` project (v0.3.0) — a network security scanner MCP server providing environmental awareness for an AGI cluster with defense-grade federal compliance capabilities.

## Key Knowledge

### Project Identity
- **Name:** `network-scanner-mcp`
- **Version:** 0.3.0
- **License:** MIT
- **Author:** AGI System
- **Python:** 3.10+
- **Build system:** hatchling
- **Package path:** `src/network_scanner_mcp/`
- **Entry points:** `network-scanner-mcp` (server), `network-scanner-daemon` (alert daemon)

### Architecture
| Layer | File | Responsibility |
|---|---|---|
| **MCP Server** | `server.py` | FastMCP server, `DeviceRegistry` (thread-safe), 16+ MCP tools |
| **Scanner** | `scanner.py` | ARP scanning, port scanning, hostname resolution, ICMP ping |
| **Utilities** | `utils.py` | Config/env parsing, network detection, JSON persistence, MAC normalization |
| **Daemon** | `alert_daemon.py` | Continuous monitoring loop with voice (edge-tts) + node-chat alerts |
| **Compliance** | `compliance/` | 6 modules: SCAP, CIS benchmarks, NIST CSF, Zero Trust, NIST 800-53, CVSS/SSVC/KEV |

### Core Capabilities
1. **Device Discovery** — ARP scanning via `arp-scan`, MAC vendor lookup, hostname resolution, device history tracking
2. **Port Scanning** — Async concurrent port scanning with banner grabbing and service fingerprinting
3. **Cluster Monitoring** — Ping-based health checks on configured cluster nodes
4. **Alert Daemon** — Continuous background monitoring with voice alerts + cluster broadcast via node-chat
5. **Defense Compliance** — SCAP (XCCDF 1.2 / OVAL 5.11 / CPE 2.3), CIS Benchmarks, NIST CSF Asset Inventory, Zero Trust Assessment (NIST 800-207 / DISA ZTA), NIST 800-53 Control Mapping, CVSS v3.1 + SSVC + KEV scoring

### Technology Choices
- **MCP Framework:** `fastmcp>=0.1.0`
- **Network Detection:** `netifaces>=0.11.0`
- **HTTP Client:** `aiohttp>=3.9.0`
- **Optional:** `mac-vendor-lookup` for MAC vendor identification
- **System Dependency:** `arp-scan` (required), `edge-tts` + `mpv` (optional voice)
- **Test Framework:** `pytest` + `pytest-asyncio` + `pytest-cov`
- **CI:** GitHub Actions (lint with ruff, security with bandit/pip-audit, type-check with mypy)

### Configuration Convention
- All config via environment variables (e.g., `NETWORK_SCANNER_DATA_DIR`, `NETWORK_INTERFACE`, `CLUSTER_NODES_JSON`)
- Data persistence: JSON files in `NETWORK_SCANNER_DATA_DIR` (default: `$AGENTIC_SYSTEM_PATH/databases/network-scanner/`)
- Device MAC addresses normalized to uppercase colon-separated format (`AA:BB:CC:DD:EE:FF`)
- Cluster nodes configured via JSON file or `CLUSTER_NODES_JSON` env var
- Supported device types: `trusted`, `iot`, `guest`, `infrastructure`

### Data Files
- `device_history.json` — All discovered devices with metadata (MAC, IP, vendor, hostname, first/last seen, ports, services)
- `known_devices.json` — Manually trusted/labeled devices
- `cluster_nodes.json` — Cluster node configuration (name, role, type)
- `alert_history.json` — Alert log (max 1000 entries)
- `pending_alerts.json` — Queued alerts for delivery

### Compliance Modules Detail
| Module | Functions | Standards |
|---|---|---|
| `scap_output.py` | `generate_xccdf_results()`, `generate_oval_definitions()`, `identify_cpe()` | NIST SP 800-126 Rev. 3, XCCDF 1.2, OVAL 5.11, CPE 2.3 |
| `cis_benchmarks.py` | `run_cis_assessment()`, `generate_cis_report()` | CIS Cisco IOS / Juniper OS / CIS Controls v8 |
| `nist_csf_inventory.py` | `build_asset_inventory()`, `classify_asset()`, `calculate_risk_score()` | NIST CSF v1.1, ID.AM-1 through ID.AM-5, FIPS 199 |
| `zero_trust.py` | `assess_zero_trust_posture()`, `generate_zt_roadmap()` | NIST SP 800-207, DISA ZTA, CISA ZT Maturity Model, OMB M-22-09 |
| `nist_800_53.py` | `map_findings_to_controls()`, `generate_poam()` | NIST SP 800-53 Rev. 5, 7 control families (AC, CA, CM, PM, RA, SC, SI) |
| `vuln_scoring.py` | `score_vulnerability()`, `prioritize_vulnerabilities()` | CVSS v3.1 (base/temporal/environmental), SSVC, CISA KEV |

### Test Structure (7 files, ~150 tests)
- **test_utils.py** — Config, MAC normalization, timestamps, JSON I/O, logging, network detection
- **test_scanner.py** — ARP scan, port scan, hostname resolution, ping, full device scan
- **test_mcp_tools.py** — All MCP tool endpoints (device discovery, info, topology, port scanning, cluster monitoring, utilities)
- **test_error_handling.py** — Error paths, corrupted files, race conditions, edge cases, data integrity
- **test_device_registry.py** — Thread-safe registry with concurrency tests, persistence, MAC normalization
- **conftest.py** — Rich fixtures: temp dirs, mock ARP data, populated registries

## Recent Actions
1. **Full project inspection completed** — Read all 12 source files, 7 test files, configuration, CI workflow, systemd service file, and README
2. **Identified comprehensive architecture** — The project has a clean modular design with separation between scanning, compliance, and server layers
3. **Found several concerns:**
   - `server.py` is 1331 lines and was truncated during reading; compliance MCP tools weren't fully visible
   - CI pipeline uses `|| true` on all lint/security/type-check steps — failures suppressed
   - No `requirements.txt` exists (uses `pyproject.toml` with hatchling), so CI security checks won't find it
   - Systemd service file hardcodes paths (`/mnt/agentic-system/`) — won't work without modification
   - Alert daemon has some hardcoded paths and assumptions about the agentic-system directory structure

### Git History (from snapshot)
- `f086c38` — Update README with project image and badges
- `710db9a` — Fix: eliminate dead code, fix parameter shadowing, fix MAC-to-IP resolution bugs
- `3840ce2` — Fix: resolve parameter shadowing crash in discover_network()
- `2ebe106` — Fix: SNMP UDP, live KEV feed, honest OVAL/ZTA/compliance scoring
- `f8d5bac` — Remove network awareness ASCII art from README

## Current Plan
No active development plan was established during this session. The user asked for a project inspection, which has been completed. The summary above captures the full project state for future reference.

### Potential Next Steps (if user requests)
1. Read the truncated portion of `server.py` to see compliance MCP tool implementations
2. Run tests to verify current state: `pytest -v`
3. Address CI pipeline issues (`|| true` suppression, missing `requirements.txt`)
4. Review and harden the compliance modules for any gaps
5. Update systemd service file for more portable deployment

---

## Summary Metadata
**Update time**: 2026-05-23T19:53:02.389Z 
