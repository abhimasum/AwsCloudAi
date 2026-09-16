# AWS Resources Cleanup Guide

After your learning/testing is complete, you can easily clean up all AWS resources to avoid unnecessary costs.

## ⚠️ Important: This will DELETE all resources!

Running this workflow will permanently delete:
- ✓ RDS PostgreSQL Database
- ✓ OpenSearch Domain
- ✓ ECR Repositories (all Docker images)
- ✓ S3 Buckets (all stored documents)
- ✓ ECS Cluster and Services
- ✓ CloudWatch Log Groups
- ✓ Security Groups

**This action is irreversible!** All data will be lost.

---

## How to Clean Up Resources

### Method 1: GitHub Actions UI (Recommended)

1. Go to your repository: `https://github.com/abhimasum/AwsCloudAi`
2. Click **Actions** tab
3. Click **Cleanup AWS Resources** workflow (left sidebar)
4. Click **Run workflow** button (top right)
5. A dialog will appear asking for confirmation:
   - **confirm_deletion**: Type exactly `DELETE_ALL` (case-sensitive)
6. Click **Run workflow**

The cleanup will start immediately and take 15-30 minutes to complete.

### Method 2: Using GitHub CLI

```bash
cd c:\Abhishek\OtherAndResearch\Learning Practical\AI\CodeBase\GoogleCloudAi\AwsCloudAi

gh workflow run cleanup-aws.yml -f confirm_deletion="DELETE_ALL"
```

### Method 3: Using AWS CLI (Manual)

If you prefer manual control, use AWS CLI directly:

```bash
# Delete ECS
aws ecs delete-service --cluster geography-ai --service orchestrator --force
aws ecs delete-cluster --cluster geography-ai

# Delete RDS
aws rds delete-db-instance --db-instance-identifier geography-ai-db --skip-final-snapshot

# Delete OpenSearch
aws opensearch delete-domain --domain-name geography-ai-os

# Delete ECR
aws ecr delete-repository --repository-name geography-ai-orchestrator --force
aws ecr delete-repository --repository-name geography-ai-retriever --force
aws ecr delete-repository --repository-name geography-ai-ingestion --force

# Delete S3
aws s3 rm s3://geography-ai-docs-YOUR_ACCOUNT_ID --recursive
aws s3api delete-bucket --bucket geography-ai-docs-YOUR_ACCOUNT_ID
```

---

## Cleanup Process Details

The cleanup workflow performs the following steps:

### 1. Confirmation Check
- Requires you to type `DELETE_ALL` to proceed
- Prevents accidental deletion

### 2. ECS Cleanup (5 seconds)
- Deletes all running services
- Deletes the ECS cluster
- Terminates containers

### 3. RDS Cleanup (10-15 minutes)
- Initiates PostgreSQL database deletion
- Skips final snapshot to save storage costs
- Takes time due to AWS internal processes

### 4. OpenSearch Cleanup (10-15 minutes)
- Deletes the OpenSearch domain
- Releases all vector indices
- Takes time due to AWS internal processes

### 5. ECR Cleanup (1-2 minutes)
- Deletes all Docker images from repositories
- Removes 3 ECR repositories:
  - `geography-ai-orchestrator`
  - `geography-ai-retriever`
  - `geography-ai-ingestion`

### 6. S3 Cleanup (1-2 minutes)
- Deletes all objects (documents) from bucket
- Removes the S3 bucket itself

### 7. CloudWatch Cleanup (30 seconds)
- Deletes all CloudWatch log groups
- Removes application logs

### 8. VPC Cleanup (30 seconds)
- Deletes security groups created for resources
- Cleans up network configuration

---

## Monitoring Cleanup Progress

### In GitHub Actions UI
1. Click **Actions** tab
2. Click the latest **Cleanup AWS Resources** run
3. Watch the logs in real-time
4. Green checkmarks indicate completed steps

### In AWS Console
Monitor resource deletion:
- **RDS**: Go to RDS Dashboard → Databases (check status)
- **OpenSearch**: Go to OpenSearch Domains (check status)
- **ECR**: Go to ECR → Repositories (verify deletion)
- **S3**: Go to S3 → Buckets (verify deletion)
- **CloudWatch**: Go to Logs → Log groups (verify deletion)

---

## Timeline Expectations

| Resource | Deletion Time |
|----------|---------------|
| ECS | ~5 seconds |
| ECR | ~1-2 minutes |
| S3 | ~1-2 minutes |
| CloudWatch Logs | ~30 seconds |
| Security Groups | ~30 seconds |
| RDS | 10-15 minutes ⏳ |
| OpenSearch | 10-15 minutes ⏳ |
| **Total** | **15-30 minutes** |

---

## Costs While Deleting

During the deletion process:
- **RDS & OpenSearch** still incur charges until fully deleted (usually 10-15 min)
- Other resources are charged until deletion completes
- After full deletion: **Zero charges**

---

## After Cleanup: What's Next?

### To Redeploy
Push code changes to master branch and the deploy workflow will automatically run:

```bash
git add .
git commit -m "Update agents"
git push origin master
```

### To Test Locally Again
All agent code remains - just reinstall dependencies:

```bash
cd agents/orchestrator_agent
pip install -r requirements.txt
python main.py
```

### To Keep GitHub Secrets
The GitHub secrets (AWS credentials, passwords) are NOT deleted. They remain for future deployments.

---

## Troubleshooting Cleanup

### Cleanup Failed / Timed Out
Run the workflow again - it's idempotent (safe to run multiple times):

```bash
gh workflow run cleanup-aws.yml -f confirm_deletion="DELETE_ALL"
```

### Resources Still Showing in AWS Console
- Give it 15-30 minutes for full deletion
- Some services like RDS and OpenSearch take time to fully clean up
- Refresh the AWS Console page periodically

### Need to Stop Cleanup Midway
1. Go to GitHub Actions
2. Click the running cleanup workflow
3. Click **Cancel workflow** (top right)
4. Resources will stay in current state (partial deletion)

### To Verify Complete Deletion
```bash
aws rds describe-db-instances --db-instance-identifier geography-ai-db
aws opensearch describe-domain --domain-name geography-ai-os
aws ecr describe-repositories --repository-names geography-ai-orchestrator
aws s3api head-bucket --bucket geography-ai-docs-YOUR_ACCOUNT_ID
```

If all return errors like "not found", cleanup is complete.

---

## Cost Savings

**Before Cleanup:**
- RDS: ~$20-30/month
- OpenSearch: ~$50-100/month
- ECS: ~$5-10/month (if running)
- S3/Other: ~$1-5/month
- **Total: ~$75-145/month**

**After Cleanup:**
- All services deleted
- **Total: $0/month** (until redeployment)

---

## Questions or Issues?

If cleanup fails:
1. Check GitHub Actions logs for errors
2. Check AWS Console for resource status
3. Try running cleanup again
4. Manually delete remaining resources via AWS Console if needed

For manual AWS CLI commands, see Method 3 above.
