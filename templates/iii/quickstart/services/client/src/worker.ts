// This is the client - it makes calls to data-service and compute-service
// In this usecase it can be thought of as an orchestrator
// but there is no requirement from iii for a central orchestrator.

import { init, getContext } from "iii-sdk";
const { registerFunction, registerTrigger, call } = init(
  process.env.III_BRIDGE_URL ?? "ws://localhost:49134",
);

// In iii all services behave as a single application so it is
// possible to set scoped state in one service and retrieve it in another.
const WORKER_VERSION = 1;
await call("state::set", {
  scope: "shared",
  key: "WORKER_VERSION",
  value: WORKER_VERSION,
});

// registerFunction is used to declare functionality to the iii engine.
// Once registered any other process connect to the engine can call this function.
// registerFunction use registerTrigger internally to make a function callable.
const health = registerFunction({ id: "client::health" }, async () => {
  const { logger } = getContext(); // Context provides logging and tracing facilities
  logger.info("Health check OK");
  return { status: 200, body: { healthy: true, timestamp: Date.now() } };
});

// registerTrigger can also be used independently to create other kinds
// of callables such as an http endpoint, or a cron job.
registerTrigger({
  trigger_type: "http",
  function_id: health.id, // This is just the string from registerFunction, ie. "client::health"
  config: { api_path: "health", http_method: "GET" },
});

registerTrigger({
  trigger_type: "cron",
  function_id: health.id,
  config: { expression: "*/30 * * * * * *" }, // Cron jobs in iii support seconds, this executes every 30 seconds
});

// The advantage of this structure is that this code can directly call
// functions that live in other services and even that use other languages.
const orchestrate = registerFunction(
  { id: "client::orchestrate" },
  async (payload) => {
    const { logger } = getContext();
    logger.info("Handling request", { payload: JSON.stringify(payload) });

    const results: { client: string; errors: any[]; [key: string]: unknown } = {
      client: "ok",
      errors: [],
    };

    // Handle both direct function calling and HTTP API calls
    const body = payload.body ?? payload;
    const data = body.data ?? body;

    // This is an async call to a Python service.
    const dataRequest = call("data-service::transform", {
      data: data,
    });
    // This is an async call to a Rust service.
    const computeRequest = call("compute-service::compute", {
      n: body.n,
    });

    // Results behave like native functions, here Promises are returned.
    const [dataResult, computeResult] = await Promise.allSettled([
      dataRequest,
      computeRequest,
    ]);

    if (dataResult.status === "fulfilled") {
      results.dataService = dataResult.value;
    } else {
      logger.error("data-service error", dataResult.reason);
      results.errors.push(dataResult.reason);
    }

    if (computeResult.status === "fulfilled") {
      results.computeService = computeResult.value;
    } else {
      logger.error("compute-service error", computeResult.reason);
      results.errors.push(computeResult.reason);
    }

    // This is a call to an external service.
    try {
      results.externalService = await call("payment-service::record", {
        charge: 0.0001,
      });
    } catch (error) {
      logger.error("payment-service error", error);
      results.errors.push(error);
    }

    results.success =
      "Success! Open services/client/src/worker.ts and ./iii-config.yaml to see how this all worked or visit https://iii.dev/docs/concepts to learn more about the concepts powering iii";

    return { status: results.errors.length > 0 ? 500 : 200, body: results };
  },
);

// And now this is creating a callable http endpoint.
registerTrigger({
  trigger_type: "http",
  function_id: orchestrate.id,
  config: { api_path: "orchestrate", http_method: "POST" },
});

console.log("Client started - listening for calls");
