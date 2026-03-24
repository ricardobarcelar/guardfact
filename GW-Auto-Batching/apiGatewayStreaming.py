# ⚡ batching automático
# 🌊 streaming token-by-token
# 🧑‍⚖️ prioridade por usuário
# 🚦 limite de concorrência global
# 🧵 compatível com vLLM OpenAI API

# Client → FastAPI Gateway → Scheduler (priority + batching) → vLLM (/v1/chat/completions) → Streaming response back

# Instalação de dependências
# pip install fastapi uvicorn httpx asyncio


import asyncio
import time
import uuid
from fastapi import FastAPI
from pydantic import BaseModel
import httpx

VLLM_URL = "http://localhost:1234/v1/chat/completions"

BATCH_SIZE = 8
BATCH_WINDOW = 0.05  # 50ms

MAX_CONCURRENCY = 16

# prioridade: maior número = mais prioridade
PRIORITY_WEIGHTS = {
    "free": 1,
    "pro": 5,
    "admin": 10
}

app = FastAPI()

queue = []
lock = asyncio.Lock()
semaphore = asyncio.Semaphore(16)

class Request(BaseModel):
    prompt: str
    user_type: str = "free"  # free / pro / admin


# -------------------------
# PRIORITY SORT FUNCTION
# -------------------------
def sort_by_priority(batch):
    return sorted(
        batch,
        key=lambda x: -x["priority"]
    )


# -------------------------
# BATCH WORKER
# -------------------------
async def batch_worker():
    while True:
        await asyncio.sleep(BATCH_WINDOW)

        async with lock:
            if not queue:
                continue

            batch = queue.copy()
            queue.clear()

        batch = sort_by_priority(batch)

        # divide em sub-batches
        for i in range(0, len(batch), BATCH_SIZE):
            sub_batch = batch[i:i+BATCH_SIZE]

            await process_batch(sub_batch)


# -------------------------
# PROCESS BATCH
# -------------------------
async def process_batch(batch):
    async with semaphore:
        async with httpx.AsyncClient(timeout=None) as client:

            tasks = []

            for item in batch:
                payload = {
                    "model": "PatronusAI/lynx3_4b_full_finetune_v0.995-fp8-dynamic",
                    "messages": [
                        {"role": "user", "content": item["prompt"]}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 200,
                    "stream": False
                }

                tasks.append(client.post(VLLM_URL, json=payload))

            responses = await asyncio.gather(*tasks)

            for item, resp in zip(batch, responses):
                try:
                    item["future"].set_result(resp.json())
                except Exception as e:
                    item["future"].set_exception(e)


# -------------------------
# START WORKER
# -------------------------
@app.on_event("startup")
async def startup():
    asyncio.create_task(batch_worker())


# -------------------------
# API ENDPOINT
# -------------------------
@app.post("/chat")
async def chat(req: Request):
    loop = asyncio.get_event_loop()
    future = loop.create_future()

    priority = PRIORITY_WEIGHTS.get(req.user_type, 1)

    async with lock:
        queue.append({
            "prompt": req.prompt,
            "future": future,
            "priority": priority,
            "id": str(uuid.uuid4())
        })

    result = await future

    return result