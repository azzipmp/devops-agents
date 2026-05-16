# Hybrid Testing Infrastructure - Main Terraform Configuration
# Provisions testing resources across AWS, Azure, and on-premise HCI

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    vsphere = {
      source  = "hashicorp/vsphere"
      version = "~> 2.4"
    }
  }
  
  backend "s3" {
    bucket = "terraform-state-hybrid-testing"
    key    = "infrastructure/terraform.tfstate"
    region = "us-west-2"
  }
}

# Variables
variable "aws_region" {
  description = "AWS region for test infrastructure"
  default     = "us-west-2"
}

variable "azure_region" {
  description = "Azure region for AKS cluster"
  default     = "eastus"
}

variable "max_spot_instances" {
  description = "Maximum AWS spot instances for parallel testing"
  default     = 50
}

variable "aks_node_count" {
  description = "Initial AKS node count"
  default     = 3
}

variable "vsphere_server" {
  description = "vCenter server endpoint"
  type        = string
  sensitive   = true
}

variable "vsphere_user" {
  description = "vSphere username"
  type        = string
  sensitive   = true
}

variable "vsphere_password" {
  description = "vSphere password"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Environment name"
  default     = "testing"
}

# AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "HybridTestInfrastructure"
      ManagedBy   = "Terraform"
    }
  }
}

# Azure Provider
provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# vSphere Provider
provider "vsphere" {
  user                 = var.vsphere_user
  password             = var.vsphere_password
  vsphere_server       = var.vsphere_server
  allow_unverified_ssl = true
}

# Modules
module "aws_test_infrastructure" {
  source = "./aws"
  
  region              = var.aws_region
  max_spot_instances  = var.max_spot_instances
  environment         = var.environment
}

module "azure_test_infrastructure" {
  source = "./azure"
  
  region         = var.azure_region
  node_count     = var.aks_node_count
  environment    = var.environment
}

module "hci_test_infrastructure" {
  source = "./vsphere"
  
  vsphere_server = var.vsphere_server
  environment    = var.environment
}

# Outputs
output "aws_spot_launch_template_id" {
  description = "Launch template ID for AWS spot instances"
  value       = module.aws_test_infrastructure.launch_template_id
}

output "azure_aks_cluster_name" {
  description = "Azure AKS cluster name"
  value       = module.azure_test_infrastructure.cluster_name
}

output "azure_aks_kubeconfig" {
  description = "AKS cluster kubeconfig"
  value       = module.azure_test_infrastructure.kubeconfig
  sensitive   = true
}

output "hci_performance_vm_ids" {
  description = "On-premise HCI VM IDs for performance testing"
  value       = module.hci_test_infrastructure.vm_ids
}

output "infrastructure_summary" {
  description = "Summary of provisioned infrastructure"
  value = {
    aws_region        = var.aws_region
    azure_region      = var.azure_region
    max_capacity      = var.max_spot_instances
    aks_nodes         = var.aks_node_count
    hci_vms          = length(module.hci_test_infrastructure.vm_ids)
  }
}
