# Getting Started

1. Install dependencies: `pnpm install`
2. Check if iii is installed: `iii --version` (if not, visit https://iii.dev/docs)
3. Run `iii -c config.yaml` to start the server (API on port 3111)
4. Try some curl commands:

   ```bash
   # Create a ticket
   curl -X POST http://localhost:3111/tickets \
     -H "Content-Type: application/json" \
     -d '{"title":"Login issue","description":"Cannot access account","priority":"high","customerEmail":"user@example.com"}'

   # List all tickets
   curl http://localhost:3111/tickets
   ```

5. Explore `/steps` folder and `config.yaml` to see how Motia works with MultiTriggers and the iii backend

Motia is just the beginning, visit https://iii.dev to learn more and stay up to date with our progress.
