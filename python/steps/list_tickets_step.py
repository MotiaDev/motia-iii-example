"""List Tickets Step - returns all tickets from state."""

from typing import Any

from motia import ApiRequest, ApiResponse, FlowContext, http

config = {
    "name": "ListTickets",
    "description": "Returns all tickets from state",
    "flows": ["support-ticket-flow"],
    "triggers": [
        http("GET", "/tickets"),
    ],
    "enqueues": [],
}


async def handler(request: ApiRequest[Any], ctx: FlowContext[Any]) -> ApiResponse[Any]:
    _ = request
    tickets = await ctx.state.list("tickets")

    ctx.logger.info("Listing tickets", {"count": len(tickets)})

    return ApiResponse(status=200, body={"tickets": tickets, "count": len(tickets)})
