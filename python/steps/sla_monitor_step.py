"""SLA Monitor Step - cron job that checks for SLA breaches on open tickets."""

from datetime import datetime, timezone
from typing import Any

from motia import FlowContext, cron

SLA_THRESHOLDS_MS = {
    "critical": 15 * 60 * 1000,       # 15 minutes
    "high": 60 * 60 * 1000,           # 1 hour
    "medium": 4 * 60 * 60 * 1000,     # 4 hours
    "low": 24 * 60 * 60 * 1000,       # 24 hours
}

config = {
    "name": "SlaMonitor",
    "description": "Cron job that checks for SLA breaches on open tickets",
    "flows": ["support-ticket-flow"],
    "triggers": [
        cron("0/30 * * * * *"),
    ],
    "enqueues": ["ticket::sla-breached"],
}


async def handler(input_data: None, ctx: FlowContext[Any]) -> None:
    _ = input_data
    ctx.logger.info("Running SLA compliance check")

    tickets = await ctx.state.list("tickets")
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    breaches = 0

    for ticket in tickets:
        if ticket.get("status") != "open" or not ticket.get("createdAt"):
            continue

        try:
            created_dt = datetime.fromisoformat(ticket["createdAt"])
            created_ms = int(created_dt.timestamp() * 1000)
        except (ValueError, TypeError):
            continue

        age_ms = now_ms - created_ms
        threshold = SLA_THRESHOLDS_MS.get(ticket.get("priority", "medium"), SLA_THRESHOLDS_MS["medium"])

        if age_ms > threshold:
            breaches += 1
            age_minutes = round(age_ms / 60_000)

            ctx.logger.warn("SLA breach detected!", {
                "ticketId": ticket["id"],
                "priority": ticket.get("priority"),
                "ageMinutes": age_minutes,
            })

            await ctx.enqueue({
                "topic": "ticket::sla-breached",
                "data": {
                    "ticketId": ticket["id"],
                    "priority": ticket.get("priority", "medium"),
                    "title": ticket.get("title", ""),
                    "ageMinutes": age_minutes,
                },
            })

    ctx.logger.info("SLA check complete", {"totalTickets": len(tickets), "breaches": breaches})
