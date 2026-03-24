# Configurar Ambiente

## Criar venv

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## Instalar dependências necessárias
pip install openai pandas nltk tqdm puncc ipykernel

## Rodar a Vllm

```bash
vllm serve Qwen/Qwen3-8B-AWQ \
  --dtype auto \
  --gpu-memory-utilization 0.9 \
  --port 1234 \
  --max-model-len 16000

vllm serve PatronusAI/lynx3_4b_full_finetune_v0.995-fp8-dynamic \
  --dtype bfloat16 \
  --gpu-memory-utilization 0.88 \
  --port 1234 \
  --max-model-len 4096
  --max-num-seqs 32
  --max-num-batched-tokens 8192
  ```

  ## Requests simultâneos

  ```python
  import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(base_url="http://localhost:1234/v1", api_key="EMPTY")

async def call(i):
    return await client.chat.completions.create(
        model="PatronusAI/lynx3_4b_full_finetune_v0.995-fp8-dynamic",
        messages=[{"role": "user", "content": f"Explique HTTP em 1 frase ({i})"}],
        max_tokens=200
    )

async def main():
    tasks = [call(i) for i in range(8)]  # 👈 batch real
    results = await asyncio.gather(*tasks)
    print(len(results))

asyncio.run(main())
```

  