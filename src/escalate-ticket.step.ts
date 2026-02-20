import { queue, api, step, FlowContext } from 'motia'
import { z } from 'zod'

/**
 * Another multi-trigger step: handles escalation from either an SLA breach
 * (queue trigger) or a manual escalation request (API trigger).
 *
 * Uses ctx.getData() to extract the shared ticketId field regardless of
 * which trigger fired.
 */

const breachSchema = z.object({
  ticketId: z.string(),
  priority: z.string(),
  title: z.string(),
  ageMinutes: z.number(),
})

const manualEscalateSchema = z.object({
  ticketId: z.string(),
  reason: z.string(),
})

/**
 * Fetches a ticket and applies escalation fields to state.
 * Returns the pre-update ticket, or null if it doesn't exist.
 */
async function escalateTicket(
  ticketId: string,
  updates: { escalationReason: string; escalationMethod: 'auto' | 'manual' },
  ctx: FlowContext<any, any>,
) {
  const existing = await ctx.state.get<Record<string, unknown>>('tickets', ticketId)
  if (!existing) return null
  await ctx.state.set('tickets', ticketId, {
    ...existing,
    escalatedTo: 'engineering-lead',
    escalatedAt: new Date().toISOString(),
    ...updates,
  })
  return existing
}

export const stepConfig = {
  name: 'EscalateTicket',
  description: 'Multi-trigger: escalates tickets from SLA breach or manual request',
  flows: ['support-ticket-flow'],
  triggers: [
    queue('ticket::sla-breached', { input: breachSchema }),
    api('POST', '/tickets/escalate', {
      bodySchema: manualEscalateSchema,
      responseSchema: {
        200: z.object({ ticketId: z.string(), escalatedTo: z.string(), message: z.string() }),
      },
    }),
  ],
  enqueues: [],
}

export const { config, handler } = step(stepConfig, async (input, ctx) => {
  const ticketId = (ctx.getData() as { ticketId: string }).ticketId
  ctx.logger.info('Escalating ticket', { ticketId, triggerType: ctx.trigger.type })

  return ctx.match({
    queue: async (breach) => {
      ctx.logger.warn('Auto-escalation from SLA breach', {
        ticketId: breach.ticketId,
        ageMinutes: breach.ageMinutes,
        priority: breach.priority,
      })
      await escalateTicket(
        breach.ticketId,
        { escalationReason: `SLA breach: ${breach.ageMinutes} minutes without resolution`, escalationMethod: 'auto' },
        ctx,
      )
    },

    http: async (request) => {
      const { ticketId, reason } = request.body
      const existing = await escalateTicket(
        ticketId,
        { escalationReason: reason, escalationMethod: 'manual' },
        ctx,
      )
      if (!existing) {
        return { status: 404, body: { error: `Ticket ${ticketId} not found` } }
      }
      ctx.logger.info('Manual escalation via API', { ticketId, reason })
      return {
        status: 200,
        body: { ticketId, escalatedTo: 'engineering-lead', message: 'Ticket escalated successfully' },
      }
    },
  })
})
