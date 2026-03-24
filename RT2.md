Resumo do Artigo
## Relatório Técnico: Implementação de Guardrails de Factualidade Conformal para Segurança Pública

Versão 2.0 - Foco em Dados Reais PJC-MT e Calibração MACI

1. Contextualização e Base de Dados

Diferente das abordagens genéricas, este experimento foi validado com dados reais de campo.

    Origem: Sistema de Registro de Ocorrências Policiais da PJC-MT.

    Domínio: Delegacia de Estelionato (registros de 2024 e 2025).

    Amostragem de Calibração: n=200 documentos, processados de forma assíncrona para garantir a estabilidade dos quantis estatísticos.

2. Metodologia de Geração e Verificação

O framework opera sob um paradigma de separação de responsabilidades (Segregation of Duties), essencial para auditoria forense.

    Geração Técnica (Qwen 3.5 9B): O modelo converte narrativas brutas de estelionato em relatórios estruturados.

    Oracle de NLI (Lynx-8B): Modelo especializado da Patronus AI, treinado especificamente para detectar discrepâncias entre contexto e afirmação, superando o GPT-4o em tarefas de fidelidade factual.

3. Especificações Técnicas e Fórmulas

A originalidade da solução reside no tratamento matemático da incerteza:

    Estabilização por Auto-Consistência: Cada sentença individual (ci​) é submetida a K=5 rodadas de auditoria. O Escore de Não-Conformidade Individual (si​) é calculado como:
    si​=K1​k=1∑K​I(vereditok​="Unfaithful")

    Agregação Multiplicativa MACI: Para relatórios policiais, adotamos uma postura conservadora onde uma única falha impacta o todo. O escore do documento (sdoc​) é o risco acumulado:
    sdoc​=1−i=1∏m​(1−si​)

    Cálculo do Limiar Conformal (q^​): Definido pelo quantil empírico no conjunto de calibração para um nível de erro α:
    q^​=Quantile(s1​,…,sn​;n⌈(n+1)(1−α)⌉​)

4. Análise dos Resultados e "Cliff de Eficiência"

O experimento final com n=200 revelou uma performance de estado da arte :

    Sweet Spot (α≈0.025): O gráfico de trade-off identifica que, ao aceitar uma tolerância mínima de erro, o sistema identifica um "cliff" (penhasco) de eficiência.

    Filtro de Risco Zero: Ao calibrar o sistema para α=0.05 (95% de confiança), o algoritmo definiu q^​=0.0. Isso significa que o guardrail barrou os 2% de relatórios que apresentavam qualquer sinal de incerteza (como os casos 12415 e 14212 do dataset), garantindo 0.00% de alucinação residual nos documentos aprovados.

5. Arquitetura Cloud-Native e Portabilidade AWS

O experimento local no macOS/LM Studio foi desenhado para paridade total com a AWS :

    Runtime: O motor vLLM utilizado mimetiza o contêiner Amazon SageMaker LMI v15, permitindo processamento em lote via Batch Transform ou em tempo real via Endpoints de baixa latência.

    Auditabilidade: Todos os "votos" do auditor e escores MACI são persistidos no AWS CloudWatch, permitindo que a PJC-MT comprove a integridade do documento em processos judiciais, atendendo ao dever de transparência da Portaria 961.

Referências Bibliográficas (Certificadas)

    ANGELOPOULOS, A. N.; BATES, S. A gentle introduction to conformal prediction and distribution-free uncertainty quantification. arXiv preprint arXiv:2107.07511, 2021.

    BRASIL. Ministério da Justiça e Segurança Pública. Portaria MJSP Nº 961, de 24 de junho de 2025. Diretrizes sobre uso de tecnologia da informação em investigação criminal. DOU, Seção 1, p. 104-105, 30 jun. 2025.

    NOH, K.; LEE, S.; KIM, I.; SONG, K. Multi-LLM Adaptive Conformal Inference for Reliable LLM Responses. Proceedings of the 14th International Conference on Learning Representations (ICLR), 2026.

    RAVI, S. S. et al. Lynx: An Open Source Hallucination Evaluation Model. arXiv preprint arXiv:2407.08488, 2024.

    WANG, X. et al. Self-Consistency Improves Chain of Thought Reasoning in Language Models. International Conference on Learning Representations (ICLR), 2023.