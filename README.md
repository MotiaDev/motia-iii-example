# Motia iii Example — Multi-Language Support

This project demonstrates the same support ticket workflow in **Node.js** (TypeScript), **Python**, and **Mixed** (both runtimes in one project). Python developers don't need npm; Node.js developers don't need Python.

## Project Structure

```
├── nodejs/              # TypeScript/Node.js implementation
│   ├── src/             # Step files (.step.ts)
│   ├── iii-config.yaml  # iii engine configuration
│   ├── package.json
│   └── tsconfig.json
├── python/              # Python implementation
│   ├── steps/           # Step files (_step.py)
│   ├── iii-config.yaml  # iii engine configuration
│   └── pyproject.toml
├── mixed/               # Node.js + Python in one project
│   ├── iii-config.yaml  # Two ExecModules (one per runtime)
│   ├── nodejs/          # HTTP API endpoints
│   └── python/          # Queue and cron steps
```

The `nodejs` and `python` directories are fully independent. The `mixed` template runs both runtimes sharing the same iii infrastructure.

## Prerequisites

- [iii CLI](https://iii.dev/docs): `iii -v`

**Node.js:**
- Node.js 18+

**Python:**
- Python 3.10+
- [uv](https://astral.sh/uv): `curl -LsSf https://astral.sh/uv/install.sh | sh`

**Mixed:**
- Both Node.js and Python prerequisites

## Running the Node.js Example

```bash
cd nodejs
npm install
iii -c iii-config.yaml
```

API available at `http://127.0.0.1:3111`

## Running the Python Example

```bash
cd python
uv sync
iii -c iii-config.yaml
```

API available at `http://127.0.0.1:3113`

## Running the Mixed Example

```bash
cd mixed
(cd nodejs && npm install)
(cd python && uv sync)
iii -c iii-config.yaml
```

Node.js handles HTTP endpoints; Python handles queue and cron triggers. API available at `http://127.0.0.1:3111`

## Try It Out

Replace the port as needed based on which implementation you're running:

```bash
# 1. List tickets (initially empty)
curl -s -X GET http://127.0.0.1:3111/tickets | jq .

# 2. Create a new support ticket
curl -s -X POST http://127.0.0.1:3111/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "title": "User reports that the login page is broken",
    "description": "Users cannot log in - getting 500 error",
    "priority": "critical",
    "customerEmail": "user@example.com"
  }' | jq .

# 3. List tickets to see the created ticket
curl -s -X GET http://127.0.0.1:3111/tickets | jq .

# 4. Manually triage/reassign the ticket (replace TICKET_ID)
curl -s -X POST http://127.0.0.1:3111/tickets/triage \
  -H "Content-Type: application/json" \
  -d '{
    "ticketId": "TICKET_ID",
    "assignee": "senior-engineer",
    "priority": "critical"
  }' | jq .

# 5. Escalate the ticket (replace TICKET_ID)
curl -s -X POST http://127.0.0.1:3111/tickets/escalate \
  -H "Content-Type: application/json" \
  -d '{
    "ticketId": "TICKET_ID",
    "reason": "Customer is enterprise tier - needs immediate attention"
  }' | jq .

# 6. List tickets to see all state changes
curl -s -X GET http://127.0.0.1:3111/tickets | jq .
```

## Step Patterns

Both implementations demonstrate the same patterns:

| Pattern | TypeScript | Python |
|---------|-----------|--------|
| HTTP POST handler | `create-ticket.step.ts` | `create_ticket_step.py` |
| HTTP GET handler | `list-tickets.step.ts` | `list_tickets_step.py` |
| Queue consumer | `notify-customer.step.ts` | `notify_customer_step.py` |
| Cron job | `sla-monitor.step.ts` | `sla_monitor_step.py` |
| Multi-trigger (queue+HTTP+cron) | `triage-ticket.step.ts` | `triage_ticket_step.py` |
| Multi-trigger (queue+HTTP) | `escalate-ticket.step.ts` | `escalate_ticket_step.py` |

## Learn More

- [Motia Documentation](https://www.motia.dev/docs)
- [iii Engine Documentation](https://iii.dev/docs)
- [iii GitHub Repository](https://github.com/iii-hq/iii)

## Windows Binaries

We do not yet have an installer for iii on Windows. The binary can be downloaded from the Github Releases page: https://github.com/iii-hq/iii/releases/latest
