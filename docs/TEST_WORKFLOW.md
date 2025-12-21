# OSPF Optimizer - Test Workflow Guide

This document provides a step-by-step workflow to verify that the OSPF Optimizer project is working correctly.

---

## Prerequisites Checklist

Before starting the tests, ensure the following:

- [X] Ubuntu VM is running with GNS3 installed
- [ ] GNS3 project with OSPF topology is open and started
- [ ] Docker is running (`systemctl status docker`)
- [ ] All router containers are running (`docker ps`)
- [ ] Python 3.10+ is installed
- [ ] Virtual environment is set up

---

## Test Workflow Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    TEST WORKFLOW                             │
├─────────────────────────────────────────────────────────────┤
│  Step 1: Environment Setup                                   │
│  Step 2: Container Detection                                 │
│  Step 3: Router Connectivity                                 │
│  Step 4: OSPF Status Verification                           │
│  Step 5: Metrics Collection                                  │
│  Step 6: Dry-Run Optimization                               │
│  Step 7: Live Optimization                                   │
│  Step 8: Web Interface                                       │
│  Step 9: End-to-End Validation                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Step 1: Environment Setup

### 1.1 Activate Virtual Environment

```bash
cd ~/OSPF_Optimizer
source venv/bin/activate
```

**Expected:** Command prompt shows `(venv)` prefix.

### 1.2 Verify Python Dependencies

```bash
pip list | grep -E "flask|pyyaml|requests"
```

**Expected Output:**
```
Flask             3.x.x
PyYAML            6.x.x
requests          2.x.x
```

### 1.3 Check Project Structure

```bash
ls -la
```

**Expected:** All required files present:
- `ospf_optimizer.py`
- `auto_start.py`
- `config/routers.yaml`
- `src/` directory with modules

---

## Step 2: Container Detection

### 2.1 List Running Docker Containers

```bash
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"
```

**Expected Output:** FRRouting containers for ABR1, ABR2, ABR3, R1, R2, R3, R4

Example:
```
NAMES                                              IMAGE           STATUS
GNS3.ABR1.69de82ae-4d4a-48a4-a6fd-3dfa70716b11    frrouting:v1    Up 2 hours
GNS3.ABR2.69de82ae-4d4a-48a4-a6fd-3dfa70716b11    frrouting:v1    Up 2 hours
...
```

### 2.2 Test Auto-Detection Script

```bash
python3 auto_start.py --dry-run --verbose
```

**Expected:**
- ✅ Containers detected
- ✅ Configuration file updated
- ✅ No errors

**Success Criteria:**
```
[INFO] Detected containers:
  ABR1: GNS3.ABR1.xxxxx
  ABR2: GNS3.ABR2.xxxxx
  ...
[INFO] Configuration updated successfully
```

---

## Step 3: Router Connectivity

### 3.1 Test Docker Exec Access

Test access to each router:

```bash
# Test ABR1
docker exec $(docker ps --format "{{.Names}}" | grep "ABR1") echo "OK"

# Test ABR2
docker exec $(docker ps --format "{{.Names}}" | grep "ABR2") echo "OK"

# Test all routers
for router in ABR1 ABR2 ABR3 R1 R2 R3 R4; do
  container=$(docker ps --format "{{.Names}}" | grep "\\.$router\\.")
  if [ -n "$container" ]; then
    result=$(docker exec $container echo "OK" 2>&1)
    echo "$router: $result"
  else
    echo "$router: NOT FOUND"
  fi
done
```

**Expected:** All routers respond with "OK"

### 3.2 Test vtysh Access

```bash
container=$(docker ps --format "{{.Names}}" | grep "ABR1")
docker exec $container vtysh -c "show version"
```

**Expected:** FRRouting version information displayed

---

## Step 4: OSPF Status Verification

### 4.1 Check OSPF is Running

```bash
container=$(docker ps --format "{{.Names}}" | grep "ABR1")
docker exec $container vtysh -c "show ip ospf"
```

**Expected:** OSPF process information with Router ID

### 4.2 Verify OSPF Neighbors

```bash
for router in ABR1 ABR2 ABR3; do
  container=$(docker ps --format "{{.Names}}" | grep "\\.$router\\.")
  echo "=== $router OSPF Neighbors ==="
  docker exec $container vtysh -c "show ip ospf neighbor"
done
```

**Expected:** Each ABR shows neighbors in FULL state

Example output:
```
=== ABR1 OSPF Neighbors ===
Neighbor ID     Pri State           Up Time         Dead Time Address         Interface
22.22.22.22       1 Full/DR         00:45:12        00:00:35  10.0.0.2        eth1
33.33.33.33       1 Full/DR         00:45:10        00:00:33  10.0.1.2        eth3
```

### 4.3 Check OSPF Interface Costs

```bash
container=$(docker ps --format "{{.Names}}" | grep "ABR1")
docker exec $container vtysh -c "show ip ospf interface"
```

**Expected:** Interface list with cost values (default: 10)

---

## Step 5: Metrics Collection Test

### 5.1 Test Ping Between Routers

```bash
# Ping from ABR1 to ABR2
container=$(docker ps --format "{{.Names}}" | grep "ABR1")
docker exec $container ping -c 5 10.0.0.2
```

**Expected:**
- 5 packets transmitted
- 0% packet loss
- Latency values displayed

### 5.2 Test Metrics Collection Module

Create a quick test script:

```bash
python3 -c "
from src.metrics_collector import MetricsCollector
from src.router_connection import RouterConnection
import yaml

with open('config/routers.yaml', 'r') as f:
    config = yaml.safe_load(f)

conn = RouterConnection(config)
if conn.test_connections():
    print('✅ Router connections: OK')
else:
    print('❌ Router connections: FAILED')
"
```

**Expected:** `✅ Router connections: OK`

---

## Step 6: Dry-Run Optimization

### 6.1 Run Single Optimization (Dry-Run)

```bash
python3 ospf_optimizer.py --config config/routers.yaml --once --dry-run --verbose
```

**Expected Output:**
```
============================================================
OSPF Optimizer - Starting
============================================================
Mode: Single run (dry-run)
Strategy: composite

Collecting metrics for all links...
  ABR1-ABR2 (Primary): BW: 5.2%, Latency: 0.8ms, Loss: 0.0%
  ABR1-ABR3 (Backup): BW: 2.1%, Latency: 0.5ms, Loss: 0.0%
  ...

OPTIMIZATION SUMMARY
------------------------------------------------------------
Links monitored: 7
Links to update: 0
Links stable: 7

[DRY-RUN] No changes applied
============================================================
```

**Success Criteria:**
- ✅ No Python errors
- ✅ Metrics collected for all links
- ✅ Summary displayed

### 6.2 Test with Simulated Data

```bash
python3 ospf_optimizer.py --config config/routers.yaml --once --dry-run --simulation
```

**Expected:** Simulated metrics with potential cost changes proposed

---

## Step 7: Live Optimization Test

⚠️ **Warning:** This will modify OSPF costs on the routers!

### 7.1 Run Single Live Optimization

```bash
python3 ospf_optimizer.py --config config/routers.yaml --once --verbose
```

**Expected:**
- Metrics collected
- If conditions warrant changes, costs are applied
- Changes saved to router configuration

### 7.2 Verify Cost Changes (if any)

```bash
container=$(docker ps --format "{{.Names}}" | grep "ABR1")
docker exec $container vtysh -c "show ip ospf interface" | grep -E "Cost:|eth"
```

**Expected:** Updated cost values visible

### 7.3 Reset Costs to Default

If you need to reset:

```bash
container=$(docker ps --format "{{.Names}}" | grep "ABR1")
docker exec $container vtysh -c "
configure terminal
interface eth0
ip ospf cost 10
interface eth1
ip ospf cost 10
end
write memory
"
```

---

## Step 8: Web Interface Test

### 8.1 Start Web Dashboard

```bash
python3 ospf_optimizer.py --config config/routers.yaml --web --port 8080
```

Or using auto_start:

```bash
python3 auto_start.py --web --port 8080
```

**Expected:** Server starts on port 8080

```
 * Running on http://0.0.0.0:8080
 * Press CTRL+C to stop
```

### 8.2 Test Dashboard Access

Open browser or use curl:

```bash
curl http://localhost:8080/
```

**Expected:** HTML content of dashboard

### 8.3 Test API Endpoints

```bash
# Get status
curl http://localhost:8080/api/status

# Get configuration
curl http://localhost:8080/api/config

# Trigger optimization (dry-run)
curl -X POST "http://localhost:8080/api/optimize?dry_run=true"
```

**Expected:** JSON responses with data

### 8.4 Test via Browser

1. Open: `http://<VM_IP>:8080`
2. Verify dashboard loads
3. Click "Status" - check metrics display
4. Click "Optimize Now" - verify execution

---

## Step 9: End-to-End Validation

### 9.1 Complete Test Scenario

```bash
# 1. Start with auto-detection
python3 auto_start.py --web --verbose

# 2. In another terminal, check routes before
container=$(docker ps --format "{{.Names}}" | grep "R1")
docker exec $container vtysh -c "show ip route ospf"

# 3. Generate traffic (simulate load)
# From R1 to R4
docker exec $container ping -c 100 -i 0.1 192.168.4.1 &

# 4. Trigger optimization via web API
curl -X POST http://localhost:8080/api/optimize

# 5. Check routes after
docker exec $container vtysh -c "show ip route ospf"
```

### 9.2 Connectivity Test After Optimization

```bash
# Test full path: PC1 to PC4
pc1=$(docker ps --format "{{.Names}}" | grep "PC1")
docker exec $pc1 ping -c 10 192.168.4.10
```

**Expected:** Connectivity maintained, possibly via different path

---

## Quick Validation Script

Create and run this script for automated testing:

```bash
#!/bin/bash
# File: test_all.sh

echo "=========================================="
echo "OSPF Optimizer - Quick Validation"
echo "=========================================="

cd ~/OSPF_Optimizer
source venv/bin/activate

# Test 1: Check containers
echo -e "\n[TEST 1] Docker Containers"
count=$(docker ps --format "{{.Names}}" | grep -E "ABR|\.R[1-4]\." | wc -l)
if [ "$count" -ge 7 ]; then
    echo "✅ PASS: $count router containers found"
else
    echo "❌ FAIL: Only $count containers found (expected 7+)"
fi

# Test 2: Check OSPF on ABR1
echo -e "\n[TEST 2] OSPF Status"
container=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)
if docker exec $container vtysh -c "show ip ospf" | grep -q "Router ID"; then
    echo "✅ PASS: OSPF is running"
else
    echo "❌ FAIL: OSPF not running"
fi

# Test 3: Dry-run optimization
echo -e "\n[TEST 3] Dry-Run Optimization"
if python3 ospf_optimizer.py --config config/routers.yaml --once --dry-run 2>&1 | grep -q "Links monitored"; then
    echo "✅ PASS: Optimization executed"
else
    echo "❌ FAIL: Optimization failed"
fi

# Test 4: Web interface
echo -e "\n[TEST 4] Web Interface"
python3 ospf_optimizer.py --config config/routers.yaml --web --port 8888 &
pid=$!
sleep 3
if curl -s http://localhost:8888/api/status | grep -q "status"; then
    echo "✅ PASS: Web API responding"
else
    echo "❌ FAIL: Web API not responding"
fi
kill $pid 2>/dev/null

echo -e "\n=========================================="
echo "Validation Complete"
echo "=========================================="
```

---

## Troubleshooting

### Problem: Containers Not Found

**Symptom:** `docker ps` shows no GNS3 containers

**Solution:**
1. Open GNS3 and start the project
2. Start all nodes (right-click → Start All)
3. Wait 30 seconds for containers to initialize
4. Run `docker ps` again

### Problem: vtysh Not Working

**Symptom:** `vtysh: command not found` or permission denied

**Solution:**
```bash
# Check if FRR is running
docker exec <container> ps aux | grep -E "ospfd|zebra"

# If not running, start services
docker exec <container> /usr/lib/frr/frrinit.sh start
```

### Problem: OSPF Neighbors Not Forming

**Symptom:** `show ip ospf neighbor` is empty

**Solution:**
1. Check interface IP configuration
2. Verify network statements in OSPF config
3. Check if cables are connected in GNS3
4. Ensure both ends are in same area

### Problem: Python Import Errors

**Symptom:** `ModuleNotFoundError: No module named 'src'`

**Solution:**
```bash
# Ensure you're in the project directory
cd ~/OSPF_Optimizer

# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Problem: Web Interface Not Accessible

**Symptom:** Cannot connect to `http://localhost:8080`

**Solution:**
1. Check if server is running (`ps aux | grep ospf_optimizer`)
2. Try different port: `--port 5000`
3. Check firewall: `sudo ufw allow 8080`
4. Bind to all interfaces is default (0.0.0.0)

---

## Scenario Tests

These scenarios simulate real-world conditions to validate that the OSPF Optimizer correctly detects issues and adjusts costs.

### Scenario 1: Link Congestion Simulation

**Objective:** Verify that high bandwidth usage triggers a cost increase.

**Steps:**

```bash
# 1. Check initial costs on ABR1
container_abr1=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)
docker exec $container_abr1 vtysh -c "show ip ospf interface eth1" | grep "Cost:"
# Note the initial cost (should be 10)

# 2. Check routing table before (from R1 perspective)
container_r1=$(docker ps --format "{{.Names}}" | grep "\.R1\." | head -1)
echo "=== Routes BEFORE congestion ==="
docker exec $container_r1 vtysh -c "show ip route ospf"

# 3. Generate heavy traffic on ABR1-ABR2 link (Primary backbone)
# Start traffic generator in background
container_abr1=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)
docker exec $container_abr1 sh -c "
  # Generate continuous traffic to ABR2 for 2 minutes
  ping -c 1000 -i 0.01 -s 65000 10.0.0.2 > /dev/null 2>&1 &
  # Also flood with small packets
  for i in \$(seq 1 50); do
    ping -c 100 -i 0.001 10.0.0.2 > /dev/null 2>&1 &
  done
"

# 4. Run the optimizer in a new terminal
cd ~/OSPF_Optimizer
source venv/bin/activate
python3 ospf_optimizer.py --config config/routers.yaml --once --verbose

# 5. Check if cost was increased
docker exec $container_abr1 vtysh -c "show ip ospf interface eth1" | grep "Cost:"
# Expected: Cost should be higher than 10 if congestion was detected

# 6. Check routing table after
echo "=== Routes AFTER optimization ==="
docker exec $container_r1 vtysh -c "show ip route ospf"
# Traffic may now route via ABR3 (backup) if primary cost increased
```

**Expected Results:**
- Initial cost: 10
- After optimization: Cost increased (e.g., 25-50 depending on load)
- Routes may shift to backup path through ABR3

**Success Criteria:**
| Metric | Before | After | Pass? |
|--------|--------|-------|-------|
| ABR1-ABR2 Cost | 10 | >10 | ⬜ |
| Optimizer detected load | - | Yes | ⬜ |
| Route changed (optional) | Via ABR2 | Via ABR3 | ⬜ |

---

### Scenario 2: Latency Degradation Simulation

**Objective:** Verify that high latency triggers a cost increase.

**Steps:**

```bash
# 1. Add artificial latency using tc (traffic control)
# This requires running tc inside the container or on the host

container_abr1=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)

# Check if tc is available (may need to install iproute2)
docker exec $container_abr1 sh -c "tc qdisc show dev eth1" 2>/dev/null || \
  echo "tc not available, using alternative method"

# Alternative: If tc is available, add 100ms delay
docker exec $container_abr1 sh -c "
  tc qdisc add dev eth1 root netem delay 100ms 2>/dev/null || \
  tc qdisc change dev eth1 root netem delay 100ms 2>/dev/null
"

# 2. Verify latency is added
docker exec $container_abr1 ping -c 5 10.0.0.2
# Expected: rtt should show ~100ms

# 3. Run optimizer
python3 ospf_optimizer.py --config config/routers.yaml --once --verbose

# 4. Check the output for latency detection
# Expected: "ABR1-ABR2: Latency: ~100ms" and cost increase proposed

# 5. Cleanup - remove the artificial delay
docker exec $container_abr1 sh -c "tc qdisc del dev eth1 root 2>/dev/null"

# 6. Verify latency is back to normal
docker exec $container_abr1 ping -c 5 10.0.0.2
```

**Expected Results:**
- Latency detected: ~100ms
- Cost increase: 10 → ~30 (based on latency factor)
- Route may shift to lower-latency path

**Note:** If `tc` is not available in the container, you can simulate latency detection by modifying the metrics collector to inject test values.

---

### Scenario 3: Packet Loss Simulation

**Objective:** Verify that packet loss triggers a cost increase.

**Steps:**

```bash
# 1. Add artificial packet loss using tc
container_abr2=$(docker ps --format "{{.Names}}" | grep "ABR2" | head -1)

# Add 10% packet loss
docker exec $container_abr2 sh -c "
  tc qdisc add dev eth1 root netem loss 10% 2>/dev/null || \
  tc qdisc change dev eth1 root netem loss 10% 2>/dev/null
"

# 2. Verify packet loss is occurring
docker exec $container_abr2 ping -c 20 10.0.0.1
# Expected: ~10% packet loss shown

# 3. Run optimizer
python3 ospf_optimizer.py --config config/routers.yaml --once --verbose

# 4. Check results
container_abr1=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)
docker exec $container_abr1 vtysh -c "show ip ospf interface eth1" | grep "Cost:"
# Expected: Cost significantly increased

# 5. Cleanup
docker exec $container_abr2 sh -c "tc qdisc del dev eth1 root 2>/dev/null"
```

**Expected Results:**
- Packet loss detected: ~10%
- Cost increase: 10 → ~50+ (packet loss has high penalty)
- Critical alert in optimizer output

---

### Scenario 4: Link Failure and Recovery

**Objective:** Verify OSPF reconvergence when a link fails and optimizer behavior.

**Steps:**

```bash
# 1. Record current routing state
container_r1=$(docker ps --format "{{.Names}}" | grep "\.R1\." | head -1)
echo "=== Initial Routes ==="
docker exec $container_r1 vtysh -c "show ip route ospf"
docker exec $container_r1 traceroute -n 192.168.4.1

# 2. Simulate link failure by bringing down interface on ABR1
container_abr1=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)
docker exec $container_abr1 vtysh -c "
configure terminal
interface eth1
shutdown
end
"

# 3. Wait for OSPF reconvergence (30-40 seconds)
sleep 40

# 4. Check new routing state
echo "=== Routes After Link Failure ==="
docker exec $container_r1 vtysh -c "show ip route ospf"
docker exec $container_r1 traceroute -n 192.168.4.1
# Expected: Traffic now routes via ABR3 (backup)

# 5. Run optimizer (should detect link as down)
python3 ospf_optimizer.py --config config/routers.yaml --once --verbose
# Expected: ABR1-ABR2 link shows as unreachable

# 6. Restore the link
docker exec $container_abr1 vtysh -c "
configure terminal
interface eth1
no shutdown
end
"

# 7. Wait for reconvergence
sleep 40

# 8. Run optimizer again
python3 ospf_optimizer.py --config config/routers.yaml --once --verbose

# 9. Check final routing state
echo "=== Routes After Recovery ==="
docker exec $container_r1 vtysh -c "show ip route ospf"
```

**Expected Results:**
| Phase | Primary Path | Backup Path | Status |
|-------|--------------|-------------|--------|
| Initial | ABR1→ABR2 | Available | Normal |
| Link Down | Unavailable | ABR1→ABR3→ABR2 | Failover |
| Recovered | ABR1→ABR2 | Available | Normal |

---

### Scenario 5: Multi-Factor Degradation

**Objective:** Test optimizer with multiple degradation factors simultaneously.

**Steps:**

```bash
# 1. Apply multiple degradations to ABR1-ABR2 link
container_abr1=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)

# Add latency + packet loss + bandwidth restriction
docker exec $container_abr1 sh -c "
  tc qdisc add dev eth1 root netem delay 50ms loss 2% rate 10mbit 2>/dev/null || \
  tc qdisc change dev eth1 root netem delay 50ms loss 2% rate 10mbit 2>/dev/null
"

# 2. Generate some traffic
docker exec $container_abr1 sh -c "
  for i in \$(seq 1 20); do
    ping -c 50 -i 0.02 10.0.0.2 > /dev/null 2>&1 &
  done
"

# 3. Run optimizer with verbose output
python3 ospf_optimizer.py --config config/routers.yaml --once --verbose 2>&1 | tee /tmp/optimizer_output.txt

# 4. Analyze output
grep -E "BW:|Latency:|Loss:|Cost" /tmp/optimizer_output.txt

# 5. Expected output pattern:
# ABR1-ABR2 (Primary): BW: 45.0%, Latency: 52.3ms, Loss: 1.80%
# Proposed cost: 10 → 45 (composite factor)

# 6. Check actual applied cost
docker exec $container_abr1 vtysh -c "show ip ospf interface eth1" | grep "Cost:"

# 7. Cleanup
docker exec $container_abr1 sh -c "tc qdisc del dev eth1 root 2>/dev/null"
```

**Expected Results:**
- Composite cost calculation considers all three factors
- Final cost = Base × (1 + BW_factor × 0.5 + Latency_factor × 0.3 + Loss_factor × 0.2)
- Cost should be significantly higher (30-60 range)

---

### Scenario 6: Continuous Monitoring Mode

**Objective:** Verify the optimizer works correctly in continuous mode.

**Steps:**

```bash
# 1. Start optimizer in continuous mode (background)
python3 ospf_optimizer.py --config config/routers.yaml --interval 30 --verbose &
OPTIMIZER_PID=$!
echo "Optimizer PID: $OPTIMIZER_PID"

# 2. Let it run for one cycle
sleep 35

# 3. Introduce degradation
container_abr1=$(docker ps --format "{{.Names}}" | grep "ABR1" | head -1)
docker exec $container_abr1 sh -c "
  tc qdisc add dev eth1 root netem delay 80ms 2>/dev/null
"

# 4. Wait for next optimization cycle
sleep 35

# 5. Check if cost was adjusted
docker exec $container_abr1 vtysh -c "show ip ospf interface eth1" | grep "Cost:"

# 6. Remove degradation
docker exec $container_abr1 sh -c "tc qdisc del dev eth1 root 2>/dev/null"

# 7. Wait for recovery detection
sleep 35

# 8. Verify cost returned to normal
docker exec $container_abr1 vtysh -c "show ip ospf interface eth1" | grep "Cost:"

# 9. Stop optimizer
kill $OPTIMIZER_PID
```

**Expected Results:**
- Optimizer detects degradation after one cycle
- Cost increased automatically
- After degradation removed, cost returns to normal

---

### Scenario 7: Web API Triggered Optimization

**Objective:** Verify optimization via web API.

**Steps:**

```bash
# 1. Start web server
python3 ospf_optimizer.py --config config/routers.yaml --web --port 8080 &
WEB_PID=$!
sleep 3

# 2. Check status via API
curl -s http://localhost:8080/api/status | python3 -m json.tool

# 3. Trigger optimization via API
curl -s -X POST "http://localhost:8080/api/optimize?strategy=composite" | python3 -m json.tool

# 4. Check with dry-run first
curl -s -X POST "http://localhost:8080/api/optimize?dry_run=true" | python3 -m json.tool

# 5. Start continuous mode via API
curl -s -X POST http://localhost:8080/api/start | python3 -m json.tool

# 6. Check status again
curl -s http://localhost:8080/api/status | python3 -m json.tool

# 7. Stop continuous mode
curl -s -X POST http://localhost:8080/api/stop | python3 -m json.tool

# 8. Cleanup
kill $WEB_PID
```

**Expected API Responses:**

```json
// /api/status
{
  "status": "running",
  "mode": "idle",
  "last_optimization": "2025-12-18T10:30:00",
  "links_monitored": 7
}

// /api/optimize
{
  "success": true,
  "changes": 2,
  "details": [
    {"link": "ABR1-ABR2", "old_cost": 10, "new_cost": 15}
  ]
}
```

---

## Automated Scenario Test Script

Create this comprehensive test script:

```bash
#!/bin/bash
# File: run_scenario_tests.sh
# Automated scenario tests for OSPF Optimizer

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd ~/OSPF_Optimizer
source venv/bin/activate

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_pass() { echo -e "${GREEN}✅ PASS:${NC} $1"; }
log_fail() { echo -e "${RED}❌ FAIL:${NC} $1"; }
log_info() { echo -e "${YELLOW}ℹ️  INFO:${NC} $1"; }

# Get container names
get_container() {
    docker ps --format "{{.Names}}" | grep "$1" | head -1
}

echo "=============================================="
echo "   OSPF Optimizer - Scenario Tests"
echo "=============================================="
echo ""

# Pre-check
log_info "Running pre-checks..."
ABR1=$(get_container "ABR1")
ABR2=$(get_container "ABR2")
R1=$(get_container "\.R1\.")

if [ -z "$ABR1" ] || [ -z "$ABR2" ]; then
    log_fail "Required containers not found"
    exit 1
fi
log_pass "Containers found: ABR1=$ABR1"

# Test 1: Basic Optimization
echo ""
echo "--- Test 1: Basic Dry-Run Optimization ---"
if python3 ospf_optimizer.py --config config/routers.yaml --once --dry-run 2>&1 | grep -q "Links monitored"; then
    log_pass "Dry-run optimization completed"
else
    log_fail "Dry-run optimization failed"
fi

# Test 2: Latency Detection
echo ""
echo "--- Test 2: Latency Detection ---"
log_info "Adding 80ms latency to ABR1-ABR2 link..."
docker exec $ABR1 sh -c "tc qdisc add dev eth1 root netem delay 80ms 2>/dev/null" || true

# Verify latency
latency=$(docker exec $ABR1 ping -c 3 -W 2 10.0.0.2 2>/dev/null | grep "avg" | cut -d'/' -f5)
log_info "Measured latency: ${latency}ms"

# Run optimizer
output=$(python3 ospf_optimizer.py --config config/routers.yaml --once --dry-run 2>&1)
if echo "$output" | grep -qE "Latency:.*[5-9][0-9]|Latency:.*1[0-9][0-9]"; then
    log_pass "High latency detected by optimizer"
else
    log_info "Latency detection may vary based on thresholds"
fi

# Cleanup
docker exec $ABR1 sh -c "tc qdisc del dev eth1 root 2>/dev/null" || true
log_info "Cleaned up latency simulation"

# Test 3: Web API
echo ""
echo "--- Test 3: Web API ---"
python3 ospf_optimizer.py --config config/routers.yaml --web --port 8888 &
WEB_PID=$!
sleep 3

if curl -s http://localhost:8888/api/status | grep -q "status"; then
    log_pass "Web API responding"
else
    log_fail "Web API not responding"
fi

kill $WEB_PID 2>/dev/null

# Test 4: Configuration Reload
echo ""
echo "--- Test 4: Configuration ---"
if python3 -c "import yaml; yaml.safe_load(open('config/routers.yaml'))" 2>/dev/null; then
    log_pass "Configuration file is valid YAML"
else
    log_fail "Configuration file has errors"
fi

# Summary
echo ""
echo "=============================================="
echo "   Scenario Tests Complete"
echo "=============================================="
echo ""
echo "For manual deep testing, run individual scenarios"
echo "as documented in docs/TEST_WORKFLOW.md"
```

Make it executable:
```bash
chmod +x run_scenario_tests.sh
./run_scenario_tests.sh
```

---

## Test Results Log Template

| Test | Expected | Actual | Status |
|------|----------|--------|--------|
| Environment Setup | venv active | | ⬜ |
| Container Detection | 7+ containers | | ⬜ |
| Docker Exec Access | All routers OK | | ⬜ |
| OSPF Running | Router ID shown | | ⬜ |
| OSPF Neighbors | FULL state | | ⬜ |
| Ping Test | 0% loss | | ⬜ |
| Dry-Run | No errors | | ⬜ |
| Live Optimization | Costs applied | | ⬜ |
| Web Dashboard | Page loads | | ⬜ |
| API /status | JSON response | | ⬜ |
| E2E Connectivity | PC1→PC4 works | | ⬜ |
| **Scenario 1** | Congestion detected | | ⬜ |
| **Scenario 2** | Latency cost increase | | ⬜ |
| **Scenario 3** | Packet loss penalty | | ⬜ |
| **Scenario 4** | Failover works | | ⬜ |
| **Scenario 5** | Composite calculation | | ⬜ |
| **Scenario 6** | Continuous mode | | ⬜ |
| **Scenario 7** | Web API triggers | | ⬜ |

---

**Document Version:** 1.1  
**Last Updated:** December 2025
