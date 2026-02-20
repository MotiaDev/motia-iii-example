import { api, queue, cron, step, FlowContext } from 'motia';
import { z } from 'zod';

/**
 * Multi-trigger step: demonstrates a single step responding to three trigger types.
 *
 * - queue:  automatically triages newly created tickets
 * - api:    lets a support agent manually re-triage any ticket
 * - cron:   periodically sweeps for untriaged tickets
 *
 * The handler uses ctx.match() to route to the correct logic per trigger,
 * and ctx.getData() to access shared fields when the input shape overlaps.
 */

const ticketEventSchema = z.object({
  ticketId: z.string(),
  title: z.string(),
  priority: z.string(),
  customerEmail: z.string(),
});

const manualTriageSchema = z.object({
  ticketId: z.string(),
  assignee: z.string(),
  priority: z.enum(['low', 'medium', 'high', 'critical']),
});

/**
 * Updates ticket state with triage fields and enqueues the triaged event.
 * Skips the state update if existing is null, but always enqueues.
 */
async function triageTicket(
  ticketId: string,
  existing: Record<string, unknown> | null,
  stateUpdates: Record<string, unknown>,
  enqueueData: { assignee: string; priority: string; title: string },
  ctx: FlowContext<any, any>,
) {
  if (existing) {
    await ctx.state.set('tickets', ticketId, {
      ...existing,
      triagedAt: new Date().toISOString(),
      ...stateUpdates,
    });
  }
  await ctx.enqueue({ topic: 'ticket::triaged', data: { ticketId, ...enqueueData } });
}

export const stepConfig = {
  name: 'TriageTicket',
  description:
    'Multi-trigger: auto-triage from queue, manual triage via API, sweep via cron',
  flows: ['support-ticket-flow'],
  triggers: [
    queue('ticket::created', { input: ticketEventSchema }),
    api('POST', '/tickets/triage', {
      bodySchema: manualTriageSchema,
      responseSchema: {
        200: z.object({
          ticketId: z.string(),
          assignee: z.string(),
          status: z.string(),
        }),
        404: z.object({ error: z.string() }),
      },
    }),
    cron('0 */5 * * * * *'), // every 5 minutes
  ],
  enqueues: ['ticket::triaged'],
};

export const { config, handler } = step(stepConfig, async (input, ctx) => {
  return ctx.match({
    queue: async (queueInput) => {
      const { ticketId, title, priority } = queueInput;
      ctx.logger.info('Auto-triaging ticket from queue', { ticketId, priority });
      const assignee = priority === 'critical' || priority === 'high' ? 'senior-support' : 'support-pool';
      const existing = await ctx.state.get<Record<string, unknown>>('tickets', ticketId);
      await triageTicket(ticketId, existing, { assignee, triageMethod: 'auto' }, { assignee, priority, title }, ctx);
      ctx.logger.info('Ticket auto-triaged', { ticketId, assignee });
    },

    http: async (request) => {
      const { ticketId, assignee, priority } = request.body;
      const existing = await ctx.state.get<Record<string, unknown>>('tickets', ticketId);
      if (!existing) {
        return { status: 404, body: { error: `Ticket ${ticketId} not found` } };
      }
      ctx.logger.info('Manual triage via API', { ticketId, assignee });
      await triageTicket(ticketId, existing, { assignee, priority, triageMethod: 'manual' }, { assignee, priority, title: existing.title as string }, ctx);
      return { status: 200, body: { ticketId, assignee, status: 'triaged' } };
    },

    cron: async () => {
      ctx.logger.info('Running untriaged ticket sweep.');
      const allTickets = await ctx.state.list<{
        id: string;
        status: string;
        priority: string;
        title: string;
        assignee?: string;
      }>('tickets');
      let swept = 0;

      for (const ticket of allTickets) {
        if (!ticket.assignee && ticket.status === 'open') {
          ctx.logger.warn('Found untriaged ticket during sweep', { ticketId: ticket.id });
          await triageTicket(
            ticket.id, ticket,
            { assignee: 'support-pool', triageMethod: 'auto-sweep' },
            { assignee: 'support-pool', priority: ticket.priority || 'medium', title: ticket.title || 'unknown' },
            ctx,
          );
          swept++;
        }
      }

      ctx.logger.info('Sweep complete', { sweptCount: swept });
    },
  });
});
