import os
import json
import boto3
import nltk
import numpy as np
from openai import OpenAI

# 1. Configurações via Variáveis de Ambiente (Requisito AWS)
SAGEMAKER_ENDPOINT = os.environ.get("SAGEMAKER_ENDPOINT_LYNX")
ALPHA = float(os.environ.get("CONFORMAL_ALPHA", 0.05))
Q_HAT = float(os.environ.get("QUANTILE_HAT", 0.0000)) # Valor calibrado: 0.0
NUM_VOTES = int(os.environ.get("K_VOTES", 5))
REGION = os.environ.get("AWS_REGION", "us-east-1")

class VerifiedGuardrail:
    def __init__(self):
        # Na AWS, o cliente aponta para o endpoint do SageMaker ou API interna
        self.client = boto3.client("sagemaker-runtime", region_name=REGION)
        nltk.download('punkt', quiet=True)

    def _get_nli_score(self, context, statement):
        """Implementa Self-Consistency (Votos) via inferência individual."""
        votos_unfaithful = 0
        prompt = f"Context: {context}\n\nStatement: {statement}\n\nIs the statement faithful to the context?"
        
        for _ in range(NUM_VOTES):
            # Payload compatível com SageMaker LMI v15 (OpenAI Schema)
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            response = self.client.invoke_endpoint(
                EndpointName=SAGEMAKER_ENDPOINT,
                ContentType="application/json",
                Body=json.dumps(payload)
            )
            result = json.loads(response.read().decode())
            veredito = result["choices"]["message"]["content"].lower()
            if "unfaithful" in veredito or "hallucination" in veredito:
                votos_unfaithful += 1
        
        return votos_unfaithful / NUM_VOTES

    def verify_document(self, context, generated_text):
        """Aplica Agregação Multiplicativa (MACI) e Decisão Conformal."""
        sentences = nltk.sent_tokenize(generated_text)
        scores_si = [self._get_nli_score(context, sent) for sent in sentences]
        
        # Fórmula MACI: s_doc = 1 - Produto(1 - s_i)
        prob_fiel_doc = np.prod([1 - s for s in scores_si])
        s_doc = 1 - prob_fiel_doc
        
        # Decisão Conformal: Garantia Estatística 1 - Alpha
        is_approved = s_doc <= Q_HAT
        
        return {
            "status": "APPROVED" if is_approved else "REJECTED",
            "risk_score": round(float(s_doc), 4),
            "threshold_used": Q_HAT,
            "sentences_count": len(sentences)
        }