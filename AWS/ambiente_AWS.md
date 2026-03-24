## Roteiro de Implantação AWS

### Passo 1: Hospedagem dos Modelos no SageMaker

    Bucket S3: Crie um bucket para armazenar os artefatos do Lynx-8B e Qwen 3.5.

    Endpoint do Auditor (Lynx):

        Utilize o contêiner de inferência DJL-LMI (URI: 763104351884.dkr.ecr.us-east-1.amazonaws.com/djl-inference:0.33.0-lmi15.0.0-cu128).

        Configure OPTION_ROLLING_BATCH=vllm e HF_MODEL_ID apontando para o S3.

        Instância recomendada: ml.g5.12xlarge para suportar as 5 rodadas de votos com baixa latência.

### Passo 2: Configuração das Variáveis de Ambiente

No console do App Runner ou na instância EC2 onde o Streamlit rodará, defina:

    SAGEMAKER_ENDPOINT_LYNX: Nome do endpoint criado.

    QUANTILE_HAT: 0.0000 (valor obtido na calibração com n=200 documentos da PJC-MT).

    CONFORMAL_ALPHA: 0.05 (para 95% de confiança).

    AWS_REGION: us-east-1 (ou a região utilizada).

### Passo 3: Segurança e Auditabilidade (MJSP 961)

    IAM Role: O serviço deve ter permissão sagemaker:InvokeEndpoint e logs:CreateLogStream.

    VPC Privada: Recomenda-se que o endpoint e a interface rodem em subnets privadas com VPC Endpoints para garantir que os dados sensíveis de estelionato nunca trafeguem pela internet pública.

    CloudWatch: Habilite o log detalhado para capturar cada decisão do MACI, servindo como evidência de integridade da cadeia de custódia digital.