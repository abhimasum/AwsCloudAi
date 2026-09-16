# AWS Setup Guide

## Prerequisites

1. **AWS Account** with Bedrock model access
2. **GitHub Account** with repository access
3. **IAM Permissions** for:
   - EC2 (ECS, VPC)
   - RDS
   - OpenSearch
   - S3
   - IAM
   - ECR
   - CloudFormation (optional)

## Step 1: Bedrock Model Access

**Update (2024):** AWS has simplified model access. Serverless foundation models are now automatically enabled across all AWS commercial regions when first invoked in your account.

**What you need to know:**
- ✅ Claude 3.5 Sonnet is auto-enabled on first invocation
- ⚠️ First-time Anthropic model users may need to submit use case details before first access
- 📋 Account administrators can use **IAM policies** and **Service Control Policies** to manage access
- 🛒 For AWS Marketplace models, a user with Marketplace permissions must invoke the model once

**Next steps:**
1. Ensure your AWS IAM user/role has Bedrock permissions (see Step 2)
2. The model will be automatically enabled when the deployment workflow first invokes it
3. If you get an access error, check AWS Bedrock console for any pending use case approval from Anthropic

**Reference:** [AWS Blog - Simplified Bedrock Model Access](https://aws.amazon.com/blogs/security/simplified-amazon-bedrock-model-access/)

## Step 2: Create IAM User for CI/CD

```bash
# Create user
aws iam create-user --user-name github-actions

# Create access key
aws iam create-access-key --user-name github-actions

# Attach policy (use AmazonEC2FullAccess, AmazonRDSFullAccess, etc.)
aws iam attach-user-policy --user-name github-actions \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

## Step 3: Configure GitHub Secrets

Add to your repository Settings → Secrets and variables → Actions:

```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_ACCOUNT_ID=123456789
AWS_REGION=us-east-1
RDS_PASSWORD=<strong-password>
OPENSEARCH_PASSWORD=<strong-password>
```

## Step 4: Deploy

Push to `master` branch:

```bash
git add .
git commit -m "Deploy AWS agents"
git push origin master
```

GitHub Actions will:
1. Create RDS PostgreSQL
2. Create OpenSearch domain
3. Build and push Docker images to ECR
4. Set up databases
5. Ingest documents

## Step 5: Deploy to ECS

After workflow completes:

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name geography-ai

# Create task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Create service
aws ecs create-service \
  --cluster geography-ai \
  --service-name orchestrator \
  --task-definition orchestrator:1 \
  --desired-count 1 \
  --launch-type FARGATE
```

## Step 6: Test Locally

```bash
# Install dependencies
cd agents/orchestrator_agent
pip install -r requirements.txt

# Set environment variables
export MODEL_ID="anthropic.claude-3-5-sonnet-20241022-v2:0"
export AWS_REGION="us-east-1"

# Run
python main.py
```

Open http://localhost:8002

## Troubleshooting

**RDS Connection Issues:**
```bash
# Check security groups
aws ec2 describe-security-groups

# Enable public access if needed
aws rds modify-db-instance \
  --db-instance-identifier geography-ai-db \
  --publicly-accessible
```

**OpenSearch Initialization Slow:**
- OpenSearch domains take 10-15 minutes to be ready
- Workflow handles this with polling and retries
- Check status: `aws opensearch describe-domain --domain-name geography-ai-os`

**Docker Build Failures:**
- Check logs in GitHub Actions
- Verify AWS credentials have ECR permissions
- Ensure Docker daemon is running locally

## Cost Optimization

**Reduce Costs:**
- Use `db.t3.micro` for RDS (free tier eligible)
- Use single-node OpenSearch for development
- Stop services when not in use
- Use S3 for long-term storage

**Cost Breakdown:**
- Bedrock: $0 (only pay per token)
- RDS: $20-30/month
- OpenSearch: $50-100/month
- S3: <$1/month
- ECS: $5-10/month
