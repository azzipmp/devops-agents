"""
Configuration Loader - Load and validate configuration
"""

import logging
import yaml
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


def load_config(config_path: str = 'config.yml') -> Dict:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
        return get_default_config()
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Loaded configuration from {config_path}")
        return config
    
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return get_default_config()


def get_default_config() -> Dict:
    """Get default configuration"""
    return {
        'cloud_providers': {
            'aws': {
                'region': 'us-west-2',
                'spot_instance_types': ['t3.large', 't3.xlarge'],
                'max_spot_instances': 50
            },
            'azure': {
                'region': 'eastus',
                'aks_cluster': 'test-aks-cluster',
                'node_pool_size': [1, 20]
            }
        },
        'on_premise': {
            'hci': {
                'provider': 'vsphere',
                'endpoint': 'vcenter.company.local',
                'datacenter': 'DC1',
                'cluster': 'TEST-CLUSTER'
            }
        },
        'test_distribution': {
            'unit_tests': 'cloud-spot',
            'integration_tests': 'azure-aks',
            'e2e_tests': 'azure-aks',
            'performance_tests': 'hci',
            'database_tests': 'hci'
        },
        'cost_optimization': {
            'max_hourly_spend': 100,
            'prefer_spot_instances': True,
            'auto_scale_down': True,
            'idle_timeout_minutes': 5
        }
    }
