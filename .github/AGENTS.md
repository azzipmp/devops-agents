# Custom Agents

This workspace provides specialized agents for hybrid test infrastructure and DevOps automation.

## Available Agents

### @cost-analyzer
**Cloud cost optimization specialist**

Use when: analyzing cloud infrastructure costs; identifying cost-saving opportunities; optimizing resource allocation for AWS, Azure, or GCP; implementing auto-scaling strategies; choosing between spot instances, reserved instances, or on-demand; calculating ROI for infrastructure changes; or reducing monthly cloud spend.

### @pipeline
**DevOps and CI/CD pipeline specialist**

Use when: creating or optimizing Jenkins, GitHub Actions, Azure DevOps, or GitLab pipelines; setting up testing infrastructure; configuring test orchestration and distribution; provisioning cloud or on-premise infrastructure with Terraform; implementing DevSecOps practices; optimizing build and deployment workflows; troubleshooting pipeline failures; or managing hybrid cloud/HCI infrastructure for testing.

### @security-scanner
**DevSecOps and security automation specialist**

Use when: implementing security scanning in CI/CD pipelines; integrating SAST, DAST, or SCA tools; configuring vulnerability scanning; setting up secret detection; implementing security policies as code; auditing infrastructure security; or troubleshooting security scan failures.

### @terraform
**Infrastructure as Code specialist**

Use when: creating or modifying Terraform configurations; provisioning cloud resources on AWS, Azure, GCP; managing infrastructure state; implementing multi-cloud deployments; configuring auto-scaling, networking, or storage; troubleshooting Terraform errors; or optimizing infrastructure costs and resource allocation.

### @test-optimizer
**Test execution optimization specialist**

Use when: analyzing test suite performance; implementing parallel test execution; distributing tests across cloud and on-premise infrastructure; reducing test execution time; optimizing test resource allocation; debugging slow tests; or implementing test sharding and batching strategies.

## Usage

Invoke agents by typing `@agent-name` in the Copilot chat, followed by your request:

```
@cost-analyzer analyze our AWS infrastructure and suggest cost reductions

@pipeline create a Jenkins pipeline for deploying microservices

@security-scanner add SAST scanning to our CI/CD pipeline

@terraform provision an AWS VPC with public and private subnets

@test-optimizer reduce our test execution time from 2 hours to under 10 minutes
```
