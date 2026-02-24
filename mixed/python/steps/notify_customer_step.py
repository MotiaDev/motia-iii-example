"""Notify Customer Step - sends a notification when a ticket has been triaged."""

import re
from typing import Any

from motia import FlowContext, queue

config = {
    "name": "NotifyCustomer",
    "description": "Sends a notification when a ticket has been triaged",
    "flows": ["support-ticket-flow"],
    "triggers": [
        queue("ticket::triaged"),
    ],
    "enqueues": [],
}


async def handler(input_data: Any, ctx: FlowContext[Any]) -> None:
    ticket_id = input_data.get("ticketId")
    assignee = input_data.get("assignee")
    priority = input_data.get("priority")
    title = input_data.get("title")

    ctx.logger.info("Sending customer notification", {"ticketId": ticket_id, "assignee": assignee})

    ticket = await ctx.state.get("tickets", ticket_id)
    customer_email = ticket.get("customerEmail", "") if ticket else ""
    redacted_email = re.sub(r"(?<=.{2}).(?=.*@)", "*", customer_email) if customer_email else "unknown"

    ctx.logger.info("Notification sent", {
        "ticketId": ticket_id,
        "assignee": assignee,
        "priority": priority,
        "title": title,
        "email": redacted_email,
    })
