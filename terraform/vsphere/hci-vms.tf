# On-Premise HCI Infrastructure for Performance-Critical Testing

variable "vsphere_server" {
  type      = string
  sensitive = true
}

variable "environment" {
  type = string
}

# Data sources for vSphere
data "vsphere_datacenter" "dc" {
  name = "DC1"
}

data "vsphere_datastore" "datastore" {
  name          = "DATASTORE-SSD"
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_compute_cluster" "cluster" {
  name          = "TEST-CLUSTER"
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_network" "network" {
  name          = "VM Network"
  datacenter_id = data.vsphere_datacenter.dc.id
}

data "vsphere_virtual_machine" "template" {
  name          = "ubuntu-22.04-template"
  datacenter_id = data.vsphere_datacenter.dc.id
}

# Resource Pool for test VMs
resource "vsphere_resource_pool" "test_pool" {
  name                    = "test-infrastructure-pool"
  parent_resource_pool_id = data.vsphere_compute_cluster.cluster.resource_pool_id
  
  cpu_reservation         = 8000  # MHz
  cpu_expandable          = true
  cpu_limit               = -1
  
  memory_reservation      = 32768 # MB
  memory_expandable       = true
  memory_limit            = -1
}

# Performance Test VMs - High CPU/Memory
resource "vsphere_virtual_machine" "performance_test_vm" {
  count            = 3
  name             = "performance-test-vm-${count.index + 1}"
  resource_pool_id = vsphere_resource_pool.test_pool.id
  datastore_id     = data.vsphere_datastore.datastore.id
  
  num_cpus             = 16
  num_cores_per_socket = 8
  memory               = 65536
  guest_id             = data.vsphere_virtual_machine.template.guest_id
  
  network_interface {
    network_id   = data.vsphere_network.network.id
    adapter_type = data.vsphere_virtual_machine.template.network_interface_types[0]
  }
  
  # High-performance disk for database testing
  disk {
    label            = "disk0"
    size             = 500
    thin_provisioned = false
    eagerly_scrub    = true
    unit_number      = 0
  }
  
  clone {
    template_uuid = data.vsphere_virtual_machine.template.id
    
    customize {
      linux_options {
        host_name = "performance-test-${count.index + 1}"
        domain    = "test.local"
      }
      
      network_interface {
        ipv4_address = "192.168.1.${100 + count.index}"
        ipv4_netmask = 24
      }
      
      ipv4_gateway = "192.168.1.1"
    }
  }
  
  extra_config = {
    "isolation.tools.copy.disable"        = "FALSE"
    "isolation.tools.paste.disable"       = "FALSE"
    "isolation.tools.setGUIOptions.enable" = "TRUE"
  }
  
  # CPU and memory reservations for consistent performance
  cpu_reservation    = 16000
  memory_reservation = 65536
  
  # Anti-affinity rule to spread VMs across hosts
  cpu_hot_add_enabled    = true
  memory_hot_add_enabled = true
}

# Load Test VMs - High Network Throughput
resource "vsphere_virtual_machine" "load_test_vm" {
  count            = 5
  name             = "load-test-vm-${count.index + 1}"
  resource_pool_id = vsphere_resource_pool.test_pool.id
  datastore_id     = data.vsphere_datastore.datastore.id
  
  num_cpus = 8
  memory   = 32768
  guest_id = data.vsphere_virtual_machine.template.guest_id
  
  network_interface {
    network_id   = data.vsphere_network.network.id
    adapter_type = "vmxnet3" # High-performance adapter
  }
  
  disk {
    label            = "disk0"
    size             = 200
    thin_provisioned = true
    unit_number      = 0
  }
  
  clone {
    template_uuid = data.vsphere_virtual_machine.template.id
    
    customize {
      linux_options {
        host_name = "load-test-${count.index + 1}"
        domain    = "test.local"
      }
      
      network_interface {
        ipv4_address = "192.168.1.${110 + count.index}"
        ipv4_netmask = 24
      }
      
      ipv4_gateway = "192.168.1.1"
    }
  }
}

# Database Test VM - Storage Optimized
resource "vsphere_virtual_machine" "database_test_vm" {
  count            = 2
  name             = "database-test-vm-${count.index + 1}"
  resource_pool_id = vsphere_resource_pool.test_pool.id
  datastore_id     = data.vsphere_datastore.datastore.id
  
  num_cpus = 8
  memory   = 32768
  guest_id = data.vsphere_virtual_machine.template.guest_id
  
  network_interface {
    network_id   = data.vsphere_network.network.id
    adapter_type = data.vsphere_virtual_machine.template.network_interface_types[0]
  }
  
  # OS disk
  disk {
    label            = "disk0"
    size             = 100
    thin_provisioned = false
    unit_number      = 0
  }
  
  # Database data disk - high performance
  disk {
    label            = "disk1"
    size             = 1000
    thin_provisioned = false
    eagerly_scrub    = true
    unit_number      = 1
  }
  
  clone {
    template_uuid = data.vsphere_virtual_machine.template.id
    
    customize {
      linux_options {
        host_name = "database-test-${count.index + 1}"
        domain    = "test.local"
      }
      
      network_interface {
        ipv4_address = "192.168.1.${120 + count.index}"
        ipv4_netmask = 24
      }
      
      ipv4_gateway = "192.168.1.1"
    }
  }
  
  # Ensure consistent storage performance
  scsi_type = "pvscsi" # High-performance SCSI controller
}

# VM Anti-Affinity Rule - Spread performance VMs across hosts
resource "vsphere_compute_cluster_vm_anti_affinity_rule" "performance_anti_affinity" {
  name                = "performance-test-anti-affinity"
  compute_cluster_id  = data.vsphere_compute_cluster.cluster.id
  virtual_machine_ids = vsphere_virtual_machine.performance_test_vm[*].id
}

# Outputs
output "vm_ids" {
  value = concat(
    vsphere_virtual_machine.performance_test_vm[*].id,
    vsphere_virtual_machine.load_test_vm[*].id,
    vsphere_virtual_machine.database_test_vm[*].id
  )
}

output "performance_vm_ips" {
  value = vsphere_virtual_machine.performance_test_vm[*].default_ip_address
}

output "load_vm_ips" {
  value = vsphere_virtual_machine.load_test_vm[*].default_ip_address
}

output "database_vm_ips" {
  value = vsphere_virtual_machine.database_test_vm[*].default_ip_address
}
