# AWS Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                           │
│              (Web Browser - Port 8002)                       │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│            Orchestrator Agent (ECS/AppRunner)                │
│    ├─ LangChain + AWS Bedrock (Claude 3.5 Sonnet)           │
│    ├─ Routes queries to SQL & Retriever agents              │
│    ├─ Returns synthesized answers                            │
│    └─ Public HTTP endpoint (8002)                            │
└────────┬──────────────────────────────────┬─────────────────┘
         │                                  │
    ┌────▼─────┐                    ┌──────▼────────┐
    │           │                    │                │
    │  SQL      │                    │  Retriever    │
    │  Agent    │                    │  Agent        │
    │ (Local)   │                    │ (ECS/AppRunner)
    │           │                    │                │
    └────┬─────┘                    └──────┬────────┘
         │                                  │
    ┌────▼──────────────────────────┬──────▼────────┐
    │                               │               │
┌───▼────────────┐          ┌──────▼─────────────┐ │
│  RDS           │          │  OpenSearch        │ │
│  PostgreSQL    │          │  Vector Store      │ │
│                │          │                    │ │
│ ┌────────────┐ │          │ ┌────────────────┐ │ │
│ │ countries  │ │          │ │ Embeddings     │ │ │
│ │ states (28)│ │          │ │ (Vector Index) │ │ │
│ │ districts  │ │          │ │                │ │ │
│ └────────────┘ │          │ └────────────────┘ │ │
└────────────────┘          └────────────────────┘ │
                                                   │
                            ┌──────────────────────┘
                            │
                    ┌───────▼───────┐
                    │  AWS Bedrock  │
                    │   Claude 3.5  │
                    │   Sonnet      │
                    └───────────────┘
```

## Components

### 1. Orchestrator Agent (Public Facing)
- **Role**: Main entry point for users
- **Technology**: FastAPI + AWS Strands Agents SDK + AWS Bedrock (boto3)
- **Input**: User queries (HTTP POST to `/run`)
- **Output**: Structured answers with source attribution
- **Responsibilities**:
  - Route queries to appropriate agent (SQL or Retriever)
  - Combine answers from both agents
  - Handle errors gracefully
  - Manage conversation context

**Orchestration Logic**:
```
Query comes in
    ↓
Is it a greeting? → Respond directly
    ↓
Is it metadata/list query? → Call SQL Agent
    ↓
Is it detailed/cultural query? → Call Retriever Agent
    ↓
Synthesize response → Return to user
```

### 2. SQL Agent (Same Process)
- **Role**: Query structured geography index
- **Technology**: AWS Strands SDK + Bedrock (boto3) + psycopg2
- **Database**: Amazon RDS PostgreSQL
- **Tools**:
  - `list_all_states()` - Get all 28 states and capitals
  - `get_state_info(state_name)` - Get details about specific state
  - `search_districts(state_name)` - Find districts in a state

**Example Queries**:
- "List all states" → Returns all 28 states with capitals
- "What is the capital of Maharashtra?" → Queries SQL
- "How many states are there?" → Queries SQL

### 3. Retriever Agent (Separate Service)
- **Role**: RAG specialist for document-grounded answers
- **Technology**: AWS Strands SDK + AWS Bedrock (boto3) + OpenSearch
- **Vector Store**: Amazon OpenSearch with HNSW index
- **Embeddings**: AWS Bedrock Titan Embeddings v2 (1536 dimensions)
- **Tools**:
  - `search_documents(query)` - Vector similarity search
  - Synthesizes answers with source attribution

**Example Queries**:
- "Tell me about the culture of Maharashtra"
- "What is the economy of Karnataka like?"
- "Describe the geography of Tamil Nadu"

### 4. Database: AWS RDS PostgreSQL
- **Instance Type**: db.t3.micro (development)
- **Tables**:
  - `countries` (1 row: India)
  - `states` (28 rows: all states + UTs)
  - `districts` (sample rows with state references)

### 5. Vector Store: Amazon OpenSearch
- **Index Name**: `geography-documents`
- **Vector Field**: `embedding` (1536 dimensions)
- **Algorithm**: HNSW with L2 distance
- **Documents Indexed**: 3 markdown files (India overview, States, Districts)
- **Chunking**: Recursive text splitter (1000 chars/chunk, 200 overlap)

### 6. Ingestion Pipeline
- **Trigger**: Runs after infrastructure provisioning in GitHub Actions
- **Process**:
  1. Fetch documents from S3 or local filesystem
  2. Split into chunks (1000 char windows with 200 char overlap)
  3. Generate embeddings using AWS Bedrock Titan Embeddings
  4. Index into OpenSearch with vector field
- **Frequency**: On-demand via GitHub Actions deployment
- **Technology**: boto3 + opensearch-py (no external dependencies)

### 7. Container Hosting Options

**Option A: AWS ECS (Fargate)**
- Managed Kubernetes alternative
- Pay per container usage
- Good for: Production, multi-container deployments

**Option B: AWS App Runner**
- Simpler container deployment
- Automatic scaling
- Good for: Quick deployments, low-to-medium traffic

## Data Flow

### Query → Answer Flow

```
User: "Tell me about Maharashtra"
   ↓
Orchestrator receives query
   ↓
Determines: This is detailed/cultural query
   ↓
Calls Retriever Agent
   ↓
Retriever Agent:
  1. Generates query embedding (Bedrock Titan)
  2. Searches OpenSearch for similar documents
  3. Retrieves top 5 matches
  4. Sends chunks to Bedrock Claude
  5. Claude synthesizes answer with citations
   ↓
Answer returned to Orchestrator
   ↓
Orchestrator returns to user with formatting
```

### Ingestion → Search Flow

```
GitHub Actions triggered (push to master)
   ↓
Workflow runs deploy-aws.yml
   ↓
Documents uploaded to S3
   ↓
Ingestion job starts
   ↓
For each document:
  1. Download from S3
  2. Split into chunks
  3. Generate embeddings with Bedrock Titan
  4. Index into OpenSearch with metadata
   ↓
Vector index ready for queries
```

## Key Differences from Azure & Google

| Aspect | Azure | Google | AWS |
|--------|-------|--------|-----|
| **LLM** | Azure OpenAI (GPT-4o) | Vertex AI (Gemini) | Bedrock (Claude) |
| **Vector Store** | Separate: AI Search | Integrated: Vertex RAG | Separate: OpenSearch |
| **SQL DB** | Azure SQL | BigQuery | RDS PostgreSQL |
| **Compute** | Container Apps | Cloud Run | ECS/AppRunner |
| **Containers** | Registry | Artifact Registry | ECR |
| **Embeddings** | Azure OpenAI | Vertex AI | Bedrock Titan |
| **Ingestion** | Workflow job | Cloud Scheduler | Lambda/ECS Task |
| **Agent Framework** | Microsoft MAF | Google ADK | LangChain |
| **Flexibility** | Medium | High (integrated) | Very High (modular) |
| **Cost at Scale** | Medium-High | Low (integrated) | Low (pay-per-use) |

## Scalability Considerations

**Current Setup (Dev)**:
- Single OpenSearch node (small)
- Single RDS instance (micro)
- Orchestrator: 1 task, 1 replica
- Retriever: 1 task, 1 replica

**Production Setup**:
- OpenSearch: 3-node cluster with replicas
- RDS: Multi-AZ deployment with read replicas
- Orchestrator: 2+ tasks across AZs
- Retriever: 2+ tasks across AZs
- Auto-scaling based on CPU/Memory
- Load balancer (Application Load Balancer)

## Security Best Practices

1. **Bedrock Access**:
   - Use IAM roles (not API keys) for ECS tasks
   - Restrict Bedrock API to specific models

2. **Database Security**:
   - Keep RDS in private VPC
   - Use security groups to restrict access
   - Enable encryption at rest/in transit
   - Use Secrets Manager for credentials

3. **OpenSearch Security**:
   - Enable fine-grained access control
   - Restrict domain to VPC
   - Use security groups

4. **Container Security**:
   - Use IAM task roles (not hardcoded credentials)
   - Scan images with Amazon ECR image scanning
   - Use private registries (no public images)

## Monitoring & Logging

**CloudWatch Metrics**:
- RDS: CPU, connections, query latency
- OpenSearch: Cluster health, indexing rate
- ECS: Container CPU, memory, task count

**Logs**:
- ECS task logs → CloudWatch
- OpenSearch logs → CloudWatch
- RDS logs → CloudWatch

**Alarms**:
- High CPU on RDS/OpenSearch
- Task failures
- Slow query latency
