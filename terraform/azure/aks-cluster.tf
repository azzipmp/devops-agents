# Azure Kubernetes Service for Integration and E2E Testing

variable "region" {
  type = string
}

variable "node_count" {
  type = number
}

variable "environment" {
  type = string
}

# Resource Group
resource "azurerm_resource_group" "test_rg" {
  name     = "rg-test-infrastructure"
  location = var.region
  
  tags = {
    Environment = var.environment
    Purpose     = "Testing Infrastructure"
  }
}

# Virtual Network
resource "azurerm_virtual_network" "test_vnet" {
  name                = "vnet-test-infrastructure"
  location            = azurerm_resource_group.test_rg.location
  resource_group_name = azurerm_resource_group.test_rg.name
  address_space       = ["10.1.0.0/16"]
  
  tags = {
    Environment = var.environment
  }
}

resource "azurerm_subnet" "aks_subnet" {
  name                 = "subnet-aks"
  resource_group_name  = azurerm_resource_group.test_rg.name
  virtual_network_name = azurerm_virtual_network.test_vnet.name
  address_prefixes     = ["10.1.1.0/24"]
}

# AKS Cluster
resource "azurerm_kubernetes_cluster" "test_cluster" {
  name                = "aks-test-cluster"
  location            = azurerm_resource_group.test_rg.location
  resource_group_name = azurerm_resource_group.test_rg.name
  dns_prefix          = "test-aks"
  kubernetes_version  = "1.28.0"
  
  default_node_pool {
    name                = "testpool"
    vm_size             = "Standard_D4s_v3"
    vnet_subnet_id      = azurerm_subnet.aks_subnet.id
    enable_auto_scaling = true
    min_count           = 1
    max_count           = 20
    node_count          = var.node_count
    os_disk_size_gb     = 100
    
    node_labels = {
      "workload" = "testing"
    }
    
    tags = {
      Environment = var.environment
    }
  }
  
  # System-assigned managed identity
  identity {
    type = "SystemAssigned"
  }
  
  # Network profile
  network_profile {
    network_plugin    = "azure"
    network_policy    = "azure"
    load_balancer_sku = "standard"
    service_cidr      = "10.2.0.0/16"
    dns_service_ip    = "10.2.0.10"
  }
  
  # Enable monitoring
  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.test_workspace.id
  }
  
  tags = {
    Environment = var.environment
  }
}

# Additional node pool for performance tests
resource "azurerm_kubernetes_cluster_node_pool" "performance_pool" {
  name                  = "perfpool"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.test_cluster.id
  vm_size               = "Standard_F16s_v2" # Compute optimized
  enable_auto_scaling   = true
  min_count             = 0
  max_count             = 10
  node_count            = 0
  os_disk_size_gb       = 100
  
  node_labels = {
    "workload" = "performance-testing"
  }
  
  node_taints = [
    "workload=performance:NoSchedule"
  ]
  
  tags = {
    Environment = var.environment
    Purpose     = "Performance Testing"
  }
}

# Log Analytics Workspace for monitoring
resource "azurerm_log_analytics_workspace" "test_workspace" {
  name                = "log-test-infrastructure"
  location            = azurerm_resource_group.test_rg.location
  resource_group_name = azurerm_resource_group.test_rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  
  tags = {
    Environment = var.environment
  }
}

# Container Registry for test images
resource "azurerm_container_registry" "test_acr" {
  name                = "acrtestinfra${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.test_rg.name
  location            = azurerm_resource_group.test_rg.location
  sku                 = "Standard"
  admin_enabled       = true
  
  tags = {
    Environment = var.environment
  }
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# Role assignment for AKS to pull from ACR
resource "azurerm_role_assignment" "aks_acr_pull" {
  principal_id                     = azurerm_kubernetes_cluster.test_cluster.kubelet_identity[0].object_id
  role_definition_name             = "AcrPull"
  scope                            = azurerm_container_registry.test_acr.id
  skip_service_principal_aad_check = true
}

# Storage Account for test artifacts
resource "azurerm_storage_account" "test_storage" {
  name                     = "sttestartifacts${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.test_rg.name
  location                 = azurerm_resource_group.test_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  
  tags = {
    Environment = var.environment
  }
}

resource "azurerm_storage_container" "test_results" {
  name                  = "test-results"
  storage_account_name  = azurerm_storage_account.test_storage.name
  container_access_type = "private"
}

# Outputs
output "cluster_name" {
  value = azurerm_kubernetes_cluster.test_cluster.name
}

output "cluster_id" {
  value = azurerm_kubernetes_cluster.test_cluster.id
}

output "kubeconfig" {
  value     = azurerm_kubernetes_cluster.test_cluster.kube_config_raw
  sensitive = true
}

output "acr_login_server" {
  value = azurerm_container_registry.test_acr.login_server
}

output "storage_account_name" {
  value = azurerm_storage_account.test_storage.name
}

output "storage_container_name" {
  value = azurerm_storage_container.test_results.name
}
