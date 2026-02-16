# Data Service - Data validation and transformation
# Demonstrates: registerFunction with Pydantic validation

import asyncio
import os
from iii import III, InitOptions, get_context
from pydantic import BaseModel, ValidationError

class TransformInput(BaseModel):
    data: dict

iii = III(
    os.environ.get("III_BRIDGE_URL", "ws://localhost:49134"),
    InitOptions(worker_name="data-service")
)

# Decorators are available
# @iii.register_function("data-service::transform")
async def transform_handler(payload: dict) -> dict:
    ctx = get_context()
    try:
        validated = TransformInput.model_validate(payload)
    except ValidationError as e:
        ctx.logger.error(f"Validation error: {e}")
        return {"error": "Invalid payload", "details": e.errors()}
    
    worker_version = await iii.call("state::get", {"scope": "shared", "key": "WORKER_VERSION"})

    ctx.logger.info("Processing data with data-service...")
    await asyncio.sleep(0.5)  # Simulates processing latency
    
    return {
        "transformed": validated.data,
        "keys": list(validated.data.keys()),
        "source": "data-service",
        "worker-version": f"worker version {worker_version}"
    }

iii.register_function("data-service::transform", transform_handler)

async def main():
    await iii.connect()
    print("Data service started - listening for calls")
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
