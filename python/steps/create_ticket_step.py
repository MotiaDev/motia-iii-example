"""Create Ticket Step - accepts a new support ticket via API and enqueues it for triage."""

import random
import string
from datetime import datetime, timezone
from typing import Any

from motia import ApiRequest, ApiResponse, FlowContext, http

config = {
    "name": "CreateTicket",
    "description": "Accepts a new support ticket via API and enqueues it for triage",
    "flows": ["support-ticket-flow"],
    "triggers": [
        http("POST", "/tickets"),
    ],
    "enqueues": ["ticket::created"],
}


async def handler(request: ApiRequest[dict[str, Any]], ctx: FlowContext[Any]) -> ApiResponse[Any]:
    body = request.body or {}
    title = body.get("title")
    description = body.get("description")
    priority = body.get("priority", "medium")
    customer_email = body.get("customerEmail")

    if not title or not description:
        return ApiResponse(status=400, body={"error": "Title and description are required"})

    random_suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    ticket_id = f"TKT-{int(datetime.now(timezone.utc).timestamp() * 1000)}-{random_suffix}"

    ticket = {
        "id": ticket_id,
        "title": title,
        "description": description,
        "priority": priority,
        "customerEmail": customer_email,
        "status": "open",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    await ctx.state.set("tickets", ticket_id, ticket)
    ctx.logger.info("Ticket created", {"ticketId": ticket_id, "priority": priority})

    await ctx.emit({
        "topic": "ticket::created",
        "data": {
            "ticketId": ticket_id,
            "title": title,
            "priority": priority,
            "customerEmail": customer_email,
        },
    })

    return ApiResponse(status=200, body={
        "ticketId": ticket_id,
        "status": "open",
        "message": "Ticket created and queued for triage",
    })
