"""Escalate Ticket Step - multi-trigger: escalates tickets from SLA breach or manual request.

Uses ctx.match() to route logic per trigger type.
"""

from datetime import datetime, timezone
from typing import Any

from motia import ApiRequest, ApiResponse, FlowContext, http, queue

config = {
    "name": "EscalateTicket",
    "description": "Multi-trigger: escalates tickets from SLA breach or manual request",
    "flows": ["support-ticket-flow"],
    "triggers": [
        queue("ticket::sla-breached"),
        http("POST", "/tickets/escalate"),
    ],
    "enqueues": [],
}


async def _escalate_ticket(
    ticket_id: str,
    updates: dict[str, Any],
    ctx: FlowContext[Any],
) -> dict[str, Any] | None:
    """Fetches a ticket and applies escalation fields to state. Returns pre-update ticket or None."""
    existing = await ctx.state.get("tickets", ticket_id)
    if not existing:
        return None
    await ctx.state.set("tickets", ticket_id, {
        **existing,
        "escalatedTo": "engineering-lead",
        "escalatedAt": datetime.now(timezone.utc).isoformat(),
        **updates,
    })
    return existing


async def handler(input_data: Any, ctx: FlowContext[Any]) -> Any:
    async def _queue_handler(breach: Any) -> None:
        ticket_id = breach.get("ticketId")
        age_minutes = breach.get("ageMinutes", 0)
        priority = breach.get("priority", "medium")

        ctx.logger.info("Escalating ticket", {"ticketId": ticket_id, "triggerType": "queue"})
        ctx.logger.warn("Auto-escalation from SLA breach", {
            "ticketId": ticket_id,
            "ageMinutes": age_minutes,
            "priority": priority,
        })

        escalated = await _escalate_ticket(
            ticket_id,
            {"escalationReason": f"SLA breach: {age_minutes} minutes without resolution", "escalationMethod": "auto"},
            ctx,
        )

        if not escalated:
            ctx.logger.error("Ticket not found during SLA escalation", {"ticketId": ticket_id, "ageMinutes": age_minutes})

    async def _http_handler(request: ApiRequest[Any]) -> ApiResponse[Any]:
        body = request.body or {}
        ticket_id = body.get("ticketId")
        reason = body.get("reason", "")

        ctx.logger.info("Escalating ticket", {"ticketId": ticket_id, "triggerType": "http"})

        existing = await _escalate_ticket(
            ticket_id,
            {"escalationReason": reason, "escalationMethod": "manual"},
            ctx,
        )

        if not existing:
            return ApiResponse(status=404, body={"error": f"Ticket {ticket_id} not found"})

        ctx.logger.info("Manual escalation via API", {"ticketId": ticket_id, "reason": reason})

        return ApiResponse(status=200, body={
            "ticketId": ticket_id,
            "escalatedTo": "engineering-lead",
            "message": "Ticket escalated successfully",
        })

    return await ctx.match({
        "queue": _queue_handler,
        "http": _http_handler,
    })
