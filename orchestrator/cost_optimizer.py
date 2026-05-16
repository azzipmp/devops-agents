"""
Cost Optimizer - Minimize infrastructure costs while maintaining performance
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class CostOptimizer:
    """Optimize test execution costs across cloud and on-premise infrastructure"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.cost_config = config.get('cost_optimization', {})
        
        # Pricing per vCPU hour
        self.pricing = {
            'cloud-spot': 0.03,      # AWS Spot instances
            'azure-aks': 0.05,       # Azure AKS
            'hci': 0.01,             # On-premise HCI (amortized fixed cost)
        }
        
        # Resource requirements per test category
        self.resource_requirements = {
            'lightweight': {'vcpu': 1, 'duration_minutes': 0.1},
            'integration': {'vcpu': 2, 'duration_minutes': 1.0},
            'e2e': {'vcpu': 2, 'duration_minutes': 2.0},
            'performance': {'vcpu': 8, 'duration_minutes': 10.0},
            'database': {'vcpu': 4, 'duration_minutes': 5.0},
        }
        
        self.max_hourly_spend = self.cost_config.get('max_hourly_spend', 100)
    
    async def optimize_distribution(
        self,
        categorized_tests: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Calculate cost-optimized distribution of tests
        
        Strategy:
        1. Use on-premise HCI for baseline capacity (fixed cost)
        2. Use cloud spot instances for burst capacity (variable cost)
        3. Prioritize cheaper infrastructure when possible
        4. Respect performance requirements
        
        Args:
            categorized_tests: Dictionary of categorized tests
            
        Returns:
            Optimized distribution mapping infrastructure to tests
        """
        logger.info("Calculating cost-optimized distribution...")
        
        distribution = {
            'cloud-spot': [],
            'azure-aks': [],
            'hci': []
        }
        
        # Calculate HCI capacity (baseline)
        hci_capacity = self._calculate_hci_capacity()
        logger.info(f"HCI baseline capacity: {hci_capacity} parallel tests")
        
        # Priority order: performance-critical tests to HCI first
        priority_order = ['performance', 'database', 'e2e', 'integration', 'lightweight']
        
        total_cost = 0.0
        hci_used = 0
        
        for category in priority_order:
            tests = categorized_tests.get(category, [])
            
            if not tests:
                continue
            
            test_count = len(tests)
            requirements = self.resource_requirements[category]
            
            # Determine optimal infrastructure for this category
            if category in ['performance', 'database']:
                # Performance-critical: prefer HCI for consistency
                if hci_used + test_count <= hci_capacity:
                    distribution['hci'].extend(tests)
                    hci_used += test_count
                    cost = self._calculate_cost('hci', test_count, requirements)
                else:
                    # HCI full, spill to AKS
                    available_hci = max(0, hci_capacity - hci_used)
                    distribution['hci'].extend(tests[:available_hci])
                    distribution['azure-aks'].extend(tests[available_hci:])
                    hci_used = hci_capacity
                    cost = (self._calculate_cost('hci', available_hci, requirements) +
                           self._calculate_cost('azure-aks', test_count - available_hci, requirements))
            
            elif category in ['e2e', 'integration']:
                # Integration tests: prefer AKS for scalability
                distribution['azure-aks'].extend(tests)
                cost = self._calculate_cost('azure-aks', test_count, requirements)
            
            else:  # lightweight
                # Unit tests: prefer cheap spot instances
                distribution['cloud-spot'].extend(tests)
                cost = self._calculate_cost('cloud-spot', test_count, requirements)
            
            total_cost += cost
            logger.info(f"  {category}: {test_count} tests, cost=${cost:.2f}")
        
        logger.info(f"Total estimated cost: ${total_cost:.2f}")
        
        if total_cost > self.max_hourly_spend:
            logger.warning(f"Cost ${total_cost:.2f} exceeds max ${self.max_hourly_spend}")
            distribution = self._reduce_costs(distribution, categorized_tests)
        
        return distribution
    
    def _calculate_hci_capacity(self) -> int:
        """Calculate available HCI capacity for parallel testing"""
        hci_config = self.config.get('on_premise', {}).get('hci', {})
        
        # Simple capacity model: assume 100 parallel tests per cluster
        # In practice, query actual resource availability
        return 100
    
    def _calculate_cost(
        self,
        infrastructure: str,
        test_count: int,
        requirements: Dict
    ) -> float:
        """
        Calculate cost for running tests on infrastructure
        
        Args:
            infrastructure: Infrastructure type
            test_count: Number of tests
            requirements: Resource requirements per test
            
        Returns:
            Estimated cost in USD
        """
        price_per_vcpu_hour = self.pricing[infrastructure]
        vcpu = requirements['vcpu']
        duration_hours = requirements['duration_minutes'] / 60.0
        
        # Parallel execution: cost = vcpu * duration * price
        # Assume tests run in parallel batches of 10
        parallel_factor = min(test_count, 10)
        batches = (test_count + parallel_factor - 1) // parallel_factor
        
        total_cost = parallel_factor * vcpu * duration_hours * price_per_vcpu_hour * batches
        
        return total_cost
    
    def _reduce_costs(
        self,
        distribution: Dict[str, List[str]],
        categorized_tests: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Reduce costs by shifting more tests to cheaper infrastructure
        
        Args:
            distribution: Current distribution
            categorized_tests: Categorized tests
            
        Returns:
            Cost-reduced distribution
        """
        logger.info("Reducing costs by shifting to cheaper infrastructure...")
        
        # Move lightweight tests from AKS to Spot
        aks_tests = distribution['azure-aks']
        lightweight_in_aks = [t for t in aks_tests if t in categorized_tests.get('lightweight', [])]
        
        if lightweight_in_aks:
            logger.info(f"Moving {len(lightweight_in_aks)} lightweight tests from AKS to Spot")
            distribution['azure-aks'] = [t for t in aks_tests if t not in lightweight_in_aks]
            distribution['cloud-spot'].extend(lightweight_in_aks)
        
        return distribution
    
    def calculate_savings(self, traditional_cost: float, optimized_cost: float) -> Dict:
        """
        Calculate cost savings from optimization
        
        Args:
            traditional_cost: Cost without optimization
            optimized_cost: Cost with optimization
            
        Returns:
            Dictionary with savings metrics
        """
        absolute_savings = traditional_cost - optimized_cost
        percentage_savings = (absolute_savings / traditional_cost * 100) if traditional_cost > 0 else 0
        
        return {
            'traditional_cost': round(traditional_cost, 2),
            'optimized_cost': round(optimized_cost, 2),
            'absolute_savings': round(absolute_savings, 2),
            'percentage_savings': round(percentage_savings, 2)
        }
