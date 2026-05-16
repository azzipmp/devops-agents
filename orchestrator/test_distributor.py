"""
Test Distributor - Intelligently categorizes and distributes tests
"""

import asyncio
import glob
import logging
import os
import re
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class TestDistributor:
    """Intelligent test distribution across infrastructure types"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.distribution_rules = config.get('test_distribution', {})
        
    async def discover_tests(self, suite: str) -> List[str]:
        """
        Discover tests from test directory
        
        Args:
            suite: Test suite name (all, unit, integration, e2e, performance)
            
        Returns:
            List of test file paths
        """
        test_dir = Path('../tests')
        
        if suite == 'all':
            patterns = ['**/test_*.py', '**/*_test.py']
        else:
            patterns = [f'{suite}/**/test_*.py', f'{suite}/**/*_test.py']
        
        tests = []
        for pattern in patterns:
            test_paths = test_dir.glob(pattern)
            tests.extend([str(p) for p in test_paths])
        
        logger.info(f"Discovered {len(tests)} test files for suite '{suite}'")
        return tests
    
    def categorize_tests(self, tests: List[str]) -> Dict[str, List[str]]:
        """
        Categorize tests by resource requirements and type
        
        Categories:
        - lightweight: Unit tests, API tests (fast, low resource)
        - integration: Integration tests, service tests (moderate resource)
        - e2e: End-to-end tests (high resource, long duration)
        - performance: Performance, load, stress tests (very high resource)
        - database: Database migrations, data tests (storage intensive)
        
        Args:
            tests: List of test file paths
            
        Returns:
            Dictionary mapping categories to test lists
        """
        categorized = {
            'lightweight': [],
            'integration': [],
            'e2e': [],
            'performance': [],
            'database': []
        }
        
        for test in tests:
            test_lower = test.lower()
            
            # Performance tests
            if any(kw in test_lower for kw in ['performance', 'load', 'stress', 'benchmark']):
                categorized['performance'].append(test)
            
            # Database tests
            elif any(kw in test_lower for kw in ['database', 'migration', 'db_', 'sql']):
                categorized['database'].append(test)
            
            # E2E tests
            elif any(kw in test_lower for kw in ['e2e', 'end_to_end', 'system', 'acceptance']):
                categorized['e2e'].append(test)
            
            # Integration tests
            elif any(kw in test_lower for kw in ['integration', 'service', 'api_integration']):
                categorized['integration'].append(test)
            
            # Unit tests (default/lightweight)
            else:
                categorized['lightweight'].append(test)
        
        logger.info("Test categorization complete:")
        for category, test_list in categorized.items():
            logger.info(f"  {category}: {len(test_list)} tests")
        
        return categorized
    
    def calculate_distribution(
        self,
        categorized_tests: Dict[str, List[str]],
        target_override: str = None
    ) -> Dict[str, List[str]]:
        """
        Calculate optimal distribution of tests across infrastructure
        
        Args:
            categorized_tests: Dictionary of categorized tests
            target_override: Force all tests to specific infrastructure
            
        Returns:
            Dictionary mapping infrastructure to test lists
        """
        if target_override:
            # Override: put all tests on specified infrastructure
            all_tests = []
            for tests in categorized_tests.values():
                all_tests.extend(tests)
            return {target_override: all_tests}
        
        # Standard distribution based on configuration
        distribution = {
            'cloud-spot': [],
            'azure-aks': [],
            'hci': []
        }
        
        # Map categories to infrastructure based on rules
        category_mapping = {
            'lightweight': self.distribution_rules.get('unit_tests', 'cloud-spot'),
            'integration': self.distribution_rules.get('integration_tests', 'azure-aks'),
            'e2e': self.distribution_rules.get('e2e_tests', 'azure-aks'),
            'performance': self.distribution_rules.get('performance_tests', 'hci'),
            'database': self.distribution_rules.get('database_tests', 'hci')
        }
        
        # Distribute tests according to mapping
        for category, tests in categorized_tests.items():
            target_infra = category_mapping.get(category, 'cloud-spot')
            distribution[target_infra].extend(tests)
        
        logger.info("Test distribution calculated:")
        for infra, tests in distribution.items():
            logger.info(f"  {infra}: {len(tests)} tests")
        
        return distribution
    
    def estimate_test_duration(self, test_path: str) -> float:
        """
        Estimate test duration based on historical data or heuristics
        
        Args:
            test_path: Path to test file
            
        Returns:
            Estimated duration in seconds
        """
        # Simple heuristic based on test type
        test_lower = test_path.lower()
        
        if 'performance' in test_lower or 'load' in test_lower:
            return 300.0  # 5 minutes
        elif 'e2e' in test_lower or 'integration' in test_lower:
            return 60.0   # 1 minute
        else:
            return 5.0    # 5 seconds for unit tests
    
    def batch_tests(self, tests: List[str], batch_size: int = 10) -> List[List[str]]:
        """
        Batch tests for parallel execution
        
        Args:
            tests: List of test paths
            batch_size: Number of tests per batch
            
        Returns:
            List of test batches
        """
        batches = []
        for i in range(0, len(tests), batch_size):
            batch = tests[i:i + batch_size]
            batches.append(batch)
        
        logger.info(f"Created {len(batches)} test batches (size={batch_size})")
        return batches
