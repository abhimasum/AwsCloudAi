# AWS Cloud AI Multi-Agent System

**Multi-agent Q&A system** for Indian geography using **AWS Strands Agents SDK**, **AWS Bedrock (Claude)**, **Amazon RDS PostgreSQL**, and **Amazon OpenSearch** with vector RAG.

---

## 🏗️ Architecture

```
User Query → Orchestrator Agent (ECS/AppRunner)
             ├─→ SQL Agent (RDS PostgreSQL: countries/states/districts index)
             └─→ Retriever Agent (OpenSearch: RAG over documents)
                 ↓
              Bedrock API (Claude 3.5 Sonnet)
```

### AWS Services Stack

| Service | Role | Why |
|---------|------|-----|
| **AWS Bedrock** | LLM reasoning | Claude 3.5 Sonnet for powerful reasoning |
| **Amazon RDS PostgreSQL** | Geography index | Fast structured queries (28 states + UTs) |
| **Amazon OpenSearch** | Vector RAG | Semantic search over documents |
| **Amazon S3** | Document storage | Source files for ingestion |
| **Amazon ECS / AppRunner** | Agent hosting | Container deployment options |
| **Amazon ECR** | Image storage | Docker images for agents |
| **AWS Lambda** | Ingestion automation | Scheduled document indexing |
| **GitHub Actions** | CI/CD | Automated build & deploy |

---

## ✅ Features

- **3 Specialized Agents**: SQL Agent (index), Retriever Agent (RAG), Orchestrator (routing)
- **AWS Strands Agents SDK**: Native AWS framework with simple routing pattern
- **28 Indian States**: All states + union territories with capitals embedded
- **Vector Search**: Native OpenSearch vector capabilities with Bedrock Titan embeddings
- **Automated CI/CD**: Push to deploy via GitHub Actions
- **Serverless-friendly**: Works on both ECS and Lambda
- **Works Out of Box**: No additional setup needed beyond basic AWS credentials

---

## 📋 Quick Start

### Prerequisites
- AWS account with Bedrock access (Claude model - auto-enabled on first use)
- GitHub account with AWS credentials configured
- Python 3.10+

### Local Development
```bash
cd agents/orchestrator_agent
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Then open http://localhost:8002

### Deployment
Push to master branch - GitHub Actions will:
1. Provision RDS, OpenSearch, S3 buckets
2. Deploy agents to ECS
3. Index documents automatically
4. Output deployment URLs

---

## 📖 Documentation

- [SETUP.md](docs/SETUP.md) - Step-by-step AWS setup guide (with latest Bedrock model access changes)
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Detailed architecture explanation
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment process details
- [CLEANUP.md](CLEANUP.md) - **Resource cleanup guide to avoid unnecessary costs** ✨

---

## 🧹 Cleanup & Cost Saving

**After learning/testing, easily clean up ALL resources:**

1. Go to GitHub Actions → **Cleanup AWS Resources**
2. Click **Run workflow**
3. Enter `DELETE_ALL` as confirmation
4. Workflow will delete RDS, OpenSearch, ECR, S3, and all other resources
5. **Costs drop to $0** within 15-30 minutes

**See [CLEANUP.md](CLEANUP.md) for detailed cleanup instructions and cost analysis.**

---

## 💰 Cost Estimate

**Monthly (Light Usage)**:
- Bedrock Claude: ~$5-20 (pay per token)
- RDS PostgreSQL: ~$20-30 (db.t3.micro)
- OpenSearch: ~$50-100 (single node)
- S3: <$1 (minimal storage)
- ECS: ~$5-10 (if using Fargate)
- **Total: ~$80-160/month**

**Idle State**:
- ~$70-100/month (RDS + OpenSearch minimum)

---

## 🚀 Deployment Status

See [DEPLOYMENT_STATUS.md](DEPLOYMENT_STATUS.md) for current deployment status.

---

## 📁 Repository Structure

```
agents/
  orchestrator_agent/      # Public-facing agent, routes queries
  retriever_agent/         # RAG specialist using OpenSearch
  sql_agent/               # Geography index queries
infra/
  setup_aws.sh            # One-time AWS setup
  setup_opensearch.py     # OpenSearch index creation
  setup_rds.py            # RDS database setup
ingestion/
  ingest.py               # Document indexing to OpenSearch
  main.py                 # Ingestion service
data/sample_docs/         # Example documents
docs/                     # Architecture + setup documentation
.github/workflows/        # GitHub Actions CI/CD pipeline
```