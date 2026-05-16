# Quick Start Guide

## Prerequisites

Before you begin, ensure you have:

- **Cloud Accounts:**
  - AWS account with admin access
  - Azure subscription
  - Service principals/IAM roles configured

- **On-Premise Access:**
  - vSphere/vCenter credentials (or Nutanix)
  - Network access to HCI infrastructure

- **Tools Installed:**
  - Terraform >= 1.5.0
  - Python >= 3.10
  - AWS CLI configured (`aws configure`)
  - Azure CLI configured (`az login`)
  - Docker (optional, for containerized orchestrator)

## Step-by-Step Setup

### 1. Clone and Install Dependencies

```powershell
# Navigate to project directory
cd C:\hybrid-test-infrastructure

# Install Python dependencies
pip install -r orchestrator\requirements.txt
pip install -r tests\requirements.txt
```

### 2. Configure Infrastructure

```powershell
# Copy example configuration
cp orchestrator\config.example.yml orchestrator\config.yml

# Edit configuration with your credentials
notepad orchestrator\config.yml
```

**Key configurations to update:**
- AWS region and credentials
- Azure subscription and resource group
- vSphere endpoint and credentials
- Cost optimization thresholds

### 3. Provision Infrastructure

```powershell
# Initialize Terraform
cd terraform
terraform init

# Review infrastructure plan
terraform plan

# Apply infrastructure
terraform apply
```

This provisions:
- ✅ AWS Auto Scaling Group with Spot instances
- ✅ Azure AKS cluster with auto-scaling
- ✅ On-premise HCI VMs (vSphere)
- ✅ Networking and security groups
- ✅ Storage for test artifacts

**Estimated provisioning time:** 10-15 minutes

### 4. Verify Infrastructure

```powershell
# Check AWS resources
aws ec2 describe-instances --filters "Name=tag:Project,Values=HybridTestInfrastructure"

# Check Azure AKS
az aks show --resource-group rg-test-infrastructure --name aks-test-cluster

# Check Terraform outputs
terraform output
```

### 5. Run Your First Test

```powershell
cd ..\orchestrator

# Run unit tests (cloud spot instances)
python main.py --suite unit

# Run all tests with cost optimization
python main.py --suite all --optimize-cost

# Run specific test on specific infrastructure
python main.py --suite performance --target hci
```

### 6. View Results

After test execution, check:
- **Console output:** Real-time test results
- **orchestrator.log:** Detailed execution logs
- **Test reports:** Generated in `tests/` directories

## Usage Examples

### Example 1: Run All Tests in Parallel

```powershell
python main.py --suite all
```

**Output:**
```
================================================================================
TEST EXECUTION REPORT
================================================================================

Status: SUCCESS
Total Tests: 5,247
Passed: 5,198 (99.07%)
Failed: 49
Skipped: 0
Duration: 387.23 seconds
Total Cost: $8.45

--------------------------------------------------------------------------------
INFRASTRUCTURE BREAKDOWN
--------------------------------------------------------------------------------

CLOUD-SPOT:
  Tests: 4,523
  Passed: 4,490
  Failed: 33
  Duration: 245.12s
  Cost: $2.15

AZURE-AKS:
  Tests: 524
  Passed: 513
  Failed: 11
  Duration: 387.23s
  Cost: $4.20

HCI:
  Tests: 200
  Passed: 195
  Failed: 5
  Duration: 612.45s
  Cost: $2.10

================================================================================
```

### Example 2: Cost-Optimized Execution

```powershell
python main.py --suite all --optimize-cost
```

This mode:
- Maximizes use of on-premise HCI (fixed cost)
- Uses cloud spot instances for overflow
- Prioritizes cheaper infrastructure
- Respects max spend limits

### Example 3: Target-Specific Execution

```powershell
# Force all tests on AWS Spot (useful for testing cloud infrastructure)
python main.py --suite all --target cloud-spot

# Run performance tests only on HCI (consistent hardware)
python main.py --suite performance --target hci
```

## CI/CD Integration

### Jenkins

```powershell
# Copy Jenkinsfile to your repository
cp pipelines\Jenkinsfile ..\your-repo\

# Configure Jenkins agents with labels:
# - cloud-spot: AWS Spot instance agents
# - azure-aks: Kubernetes agents
# - hci-performance: On-premise HCI agents
```

### GitHub Actions

Create `.github/workflows/test.yml`:

```yaml
name: Hybrid Test Execution

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r orchestrator/requirements.txt
      
      - name: Run tests
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AZURE_CREDENTIALS: ${{ secrets.AZURE_CREDENTIALS }}
        run: |
          python orchestrator/main.py --suite all --optimize-cost
```

## Monitoring and Metrics

### Real-time Monitoring

The orchestrator provides metrics on port 8080:

```powershell
# In separate terminal, start metrics server
python orchestrator/metrics_server.py

# View metrics
curl http://localhost:8080/metrics
```

**Available metrics:**
- Test execution count by infrastructure
- Cost per test suite
- Resource utilization
- Queue depths
- Failure rates

### Cost Tracking

```powershell
# Generate cost report
python orchestrator/cost_report.py --output cost-report.html

# Open in browser
start cost-report.html
```

## Troubleshooting

### Issue: Spot instances not launching

**Solution:**
```powershell
# Check spot instance requests
aws ec2 describe-spot-instance-requests

# Check Auto Scaling Group
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names test-runners-asg
```

### Issue: AKS nodes not scaling

**Solution:**
```powershell
# Check cluster autoscaler
kubectl get pods -n kube-system | grep cluster-autoscaler

# Check node pool
az aks nodepool show --resource-group rg-test-infrastructure --cluster-name aks-test-cluster --name testpool
```

### Issue: HCI VMs not accessible

**Solution:**
```powershell
# Verify vSphere connectivity
ping vcenter.company.local

# Check VM power state via Terraform
terraform state show 'module.hci_test_infrastructure.vsphere_virtual_machine.performance_test_vm[0]'
```

### Issue: Tests failing consistently

**Solution:**
```powershell
# Run in serial mode for debugging
python main.py --suite unit --serial

# Check detailed logs
type orchestrator.log

# Run specific test file
pytest tests/unit/test_example.py -v
```

## Cleanup

### Temporary Cleanup (Keep Infrastructure)

```powershell
# Clean test results only
make clean
```

### Full Cleanup (Destroy Infrastructure)

```powershell
# Destroy all infrastructure
cd terraform
terraform destroy

# Confirm when prompted
```

**Warning:** This will terminate all cloud resources and power off HCI VMs!

## Next Steps

1. **Customize Test Distribution:** Edit `orchestrator/config.yml` to match your test categories
2. **Add Your Tests:** Place tests in `tests/` directories (unit, integration, e2e, performance)
3. **Configure CI/CD:** Integrate with your CI/CD pipeline
4. **Set Up Monitoring:** Configure metrics and alerting
5. **Optimize Costs:** Review cost reports and adjust infrastructure allocation

## Support

For issues or questions:
- Check the main [README.md](README.md)
- Review logs in `orchestrator.log`
- Open an issue in your repository

---

**Estimated Setup Time:** 30-45 minutes
**Monthly Cost (Baseline):** ~$3,200 (62% savings vs all-cloud)
