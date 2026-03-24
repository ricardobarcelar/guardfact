# O cliente manda requests normais, e o gateway agrupa automaticamente em batch antes de enviar pro vLLM.

# Clientes → API Gateway (batching) → vLLM → GPU

# O gateway faz:
# - acumular requests por alguns ~50ms
# - agrupar em lote
# - enviar em paralelo ou sequencial otimizado
# - devolver respostas individuais

# Configuração do vLLM:
# --max-num-seqs 32
# --gpu-memory-utilization 0.88

# Instalação de dependências
# pip install fastapi uvicorn httpx asyncio

import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
import httpx

VLLM_URL = "http://localhost:1234/v1/chat/completions"
BATCH_SIZE = 8
TIME_WINDOW = 0.05

queue = []
lock = asyncio.Lock()
last_process_time = time.time()

class Request(BaseModel):
    prompt: str

# 🔥 worker que processa batch
async def batch_worker():
    global last_process_time
    
    while True:
        await asyncio.sleep(0.01)  # verificar a cada 10ms

        async with lock:
            if not queue:
                continue

            current_time = time.time()
            elapsed_time = current_time - last_process_time
            
            # Processar se atingiu BATCH_SIZE OU passou TIME_WINDOW
            if len(queue) >= BATCH_SIZE or elapsed_time >= TIME_WINDOW:
                batch = queue.copy()
                queue.clear()
                last_process_time = current_time
            else:
                continue

        async with httpx.AsyncClient() as client:
            tasks = []

            for item in batch:
                payload = {
                    "model": "PatronusAI/lynx3_4b_full_finetune_v0.995-fp8-dynamic",
                    "messages": [{"role": "user", "content": item["prompt"]}],
                    "max_tokens": 200,
                    "temperature": 0.2
                }

                tasks.append(client.post(VLLM_URL, json=payload))

            responses = await asyncio.gather(*tasks)

            for item, resp in zip(batch, responses):
                item["future"].set_result(resp.json())

# Lifespan context manager (substituindo on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    asyncio.create_task(batch_worker())
    print("✅ Gateway iniciado - Aguardando requests...")
    yield
    # Shutdown
    print("🛑 Gateway finalizado")

app = FastAPI(lifespan=lifespan)

@app.post("/chat")
async def chat(req: Request):
    loop = asyncio.get_event_loop()
    future = loop.create_future()

    async with lock:
        queue.append({
            "prompt": req.prompt,
            "future": future
        })

    return await future

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)