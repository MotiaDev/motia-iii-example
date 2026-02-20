# Getting Started

## Setup

1. Install dependencies: `npm install`
2. Check if iii is installed: `iii --version` (if not, visit https://iii.dev/docs)
3. Run `iii --config iii-config.yaml` to start the server (API on port 3111)
4. Try some curl commands:

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

   # 3. List tickets to see the created ticket (note the ticketId from step 2, or grab it with | jq -r '.ticketId')
   curl -s -X GET http://127.0.0.1:3111/tickets | jq .

   # 4. Manually triage/reassign the ticket (replace TICKET_ID with actual ID)
   curl -s -X POST http://127.0.0.1:3111/tickets/triage \
     -H "Content-Type: application/json" \
     -d '{
       "ticketId": "TICKET_ID",
       "assignee": "senior-engineer",
       "priority": "critical"
     }' | jq .

   # 5. Escalate the ticket (replace TICKET_ID with actual ID)
   curl -s -X POST http://127.0.0.1:3111/tickets/escalate \
     -H "Content-Type: application/json" \
     -d '{
       "ticketId": "TICKET_ID",
       "reason": "Customer is enterprise tier - needs immediate attention"
     }' | jq .

   # 6. List tickets to see all state changes
   curl -s -X GET http://127.0.0.1:3111/tickets | jq .
   ```

5. Explore `src/` folder and `iii-config.yaml` to see how Motia works with MultiTriggers and the iii backend

Motia is just the beginning, visit https://iii.dev to learn more and stay up to date with our progress.
