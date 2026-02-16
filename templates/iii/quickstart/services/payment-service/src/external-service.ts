// This is an example external service, its endpoints are being defined
// so that other services connected to iii can use them.

import { init } from "iii-sdk";
const { registerFunction } = init(
  process.env.III_BRIDGE_URL ?? "ws://localhost:49134",
);

registerFunction({ id: "payment-service::record" }, async (payload) => {
  // A real service would be defined like this.
  // const result = await fetch("https://example.com/v1/payments/record", {
  //   method: "POST",
  //   body: JSON.stringify(payload),
  // });
  return {
    status: 200,
    body: { message: "Payment recorded" },
    source: "payment-service",
  };
});

console.log("Payment service started - listening for calls");
