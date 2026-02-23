"""Triage Ticket Step - multi-trigger: auto-triage from queue, manual triage via API, sweep via cron.

Demonstrates a single step responding to three trigger types using ctx.match().
"""

from datetime import datetime, timezone
from typing import Any

from motia import ApiRequest, ApiResponse, FlowContext, cron, http, queue

config = {
    "name": "TriageTicket",
    "description": "Multi-trigger: auto-triage from queue, manual triage via API, sweep via cron",
    "flows": ["support-ticket-flow"],
    "triggers": [
        queue("ticket::created"),
        http("POST", "/tickets/triage"),
        cron("0 */5 * * * * *"),
    ],
    "enqueues": ["ticket::triaged"],
}


async def _triage_ticket(
    ticket_id: str,
    existing: dict[str, Any] | None,
    state_updates: dict[str, Any],
    enqueue_data: dict[str, Any],
    ctx: FlowContext[Any],
) -> None:
    """Updates ticket state with triage fields and emits the triaged event."""
    if not existing:
        return
    updated = {**existing, "triagedAt": datetime.now(timezone.utc).isoformat(), **state_updates}
    await ctx.state.set("tickets", ticket_id, updated)
    await ctx.emit({"topic": "ticket::triaged", "data": {"ticketId": ticket_id, **enqueue_data}})


async def handler(input_data: Any, ctx: FlowContext[Any]) -> Any:
    async def _queue_handler(data: Any) -> None:
        ticket_id = data.get("ticketId")
        title = data.get("title", "")
        priority = data.get("priority", "medium")

        ctx.logger.info("Auto-triaging ticket from queue", {"ticketId": ticket_id, "priority": priority})

        assignee = "senior-support" if priority in ("critical", "high") else "support-pool"
        existing = await ctx.state.get("tickets", ticket_id)

        await _triage_ticket(
            ticket_id, existing,
            {"assignee": assignee, "triageMethod": "auto"},
            {"assignee": assignee, "priority": priority, "title": title},
            ctx,
        )
        ctx.logger.info("Ticket auto-triaged", {"ticketId": ticket_id, "assignee": assignee})

    async def _http_handler(request: ApiRequest[Any]) -> ApiResponse[Any]:
        body = request.body or {}
        ticket_id = body.get("ticketId")
        assignee = body.get("assignee")
        priority = body.get("priority", "medium")

        existing = await ctx.state.get("tickets", ticket_id)
        if not existing:
            return ApiResponse(status=404, body={"error": f"Ticket {ticket_id} not found"})

        ctx.logger.info("Manual triage via API", {"ticketId": ticket_id, "assignee": assignee})

        await _triage_ticket(
            ticket_id, existing,
            {"assignee": assignee, "priority": priority, "triageMethod": "manual"},
            {"assignee": assignee, "priority": priority, "title": existing.get("title", "")},
            ctx,
        )
        return ApiResponse(status=200, body={"ticketId": ticket_id, "assignee": assignee, "status": "triaged"})

    async def _cron_handler() -> None:
        ctx.logger.info("Running untriaged ticket sweep.")
        tickets = await ctx.state.list("tickets")
        swept = 0

        for ticket in tickets:
            if not ticket.get("assignee") and ticket.get("status") == "open":
                ctx.logger.warn("Found untriaged ticket during sweep", {"ticketId": ticket["id"]})
                await _triage_ticket(
                    ticket["id"], ticket,
                    {"assignee": "support-pool", "triageMethod": "auto-sweep"},
                    {"assignee": "support-pool", "priority": ticket.get("priority", "medium"), "title": ticket.get("title", "unknown")},
                    ctx,
                )
                swept += 1

        ctx.logger.info("Sweep complete", {"sweptCount": swept})

    return await ctx.match({
        "queue": _queue_handler,
        "http": _http_handler,
        "cron": _cron_handler,
    })
