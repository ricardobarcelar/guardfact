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
from fastapi.responses import JSONResponse
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
        await asyncio.sleep(0.01)

        async with lock:
            if not queue:
                continue

            current_time = time.time()
            elapsed_time = current_time - last_process_time
            
            if len(queue) >= BATCH_SIZE or elapsed_time >= TIME_WINDOW:
                print(f"📦 Processando batch de {len(queue)} requests")  # DEBUG
                batch = queue.copy()
                queue.clear()
                last_process_time = current_time
            else:
                continue

        # Timeout de 300 segundos para chamadas ao vLLM
        timeout = httpx.Timeout(300.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            tasks = []

            for item in batch:
                payload = {
                    "model": "PatronusAI/lynx3_4b_full_finetune_v0.995-fp8-dynamic",
                    "messages": [{"role": "user", "content": item["prompt"]}],
                    "max_tokens": 200,
                    "temperature": 0.2
                }

                tasks.append(client.post(VLLM_URL, json=payload))

            try:
                responses = await asyncio.gather(*tasks)
                print(f"✅ Respostas recebidas: {len(responses)}")  # DEBUG
                
                for item, resp in zip(batch, responses):
                    if resp.status_code == 200:
                        item["future"].set_result(resp.json())
                    else:
                        error_msg = f"vLLM error {resp.status_code}: {resp.text[:500]}"
                        print(f"❌ {error_msg}")
                        item["future"].set_exception(Exception(error_msg))
            except Exception as e:
                print(f"❌ Erro ao chamar vLLM: {e}")  # DEBUG
                for item in batch:
                    if not item["future"].done():
                        item["future"].set_exception(e)

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

    try:
        result = await asyncio.wait_for(future, timeout=300)
        return result
    except asyncio.TimeoutError:
        return JSONResponse(status_code=504, content={"error": "Timeout na processamento"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Erro interno no gateway: {str(e)}"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)