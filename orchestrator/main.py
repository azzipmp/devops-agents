#!/usr/bin/env python3
"""
Hybrid Test Infrastructure Orchestrator
Intelligently distributes tests across cloud and on-premise infrastructure
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List

from test_distributor import TestDistributor
from cost_optimizer import CostOptimizer
from infrastructure_manager import InfrastructureManager
from config_loader import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('orchestrator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class TestOrchestrator:
    """Main orchestration engine for hybrid test infrastructure"""
    
    def __init__(self, config_path: str = 'config.yml'):
        """Initialize orchestrator with configuration"""
        self.config = load_config(config_path)
        self.distributor = TestDistributor(self.config)
        self.cost_optimizer = CostOptimizer(self.config)
        self.infra_manager = InfrastructureManager(self.config)
        
    async def run_tests(
        self,
        test_suite: str,
        target: str = None,
        optimize_cost: bool = False,
        parallel: bool = True
    ) -> Dict:
        """
        Execute test suite with intelligent distribution
        
        Args:
            test_suite: Test suite to run (all, unit, integration, e2e, performance)
            target: Specific target infrastructure (cloud-spot, azure-aks, hci)
            optimize_cost: Enable aggressive cost optimization
            parallel: Enable parallel test execution
            
        Returns:
            Dictionary with test results and execution metrics
        """
        logger.info(f"Starting test orchestration for suite: {test_suite}")
        
        # 1. Discover and categorize tests
        logger.info("Discovering tests...")
        tests = await self.distributor.discover_tests(test_suite)
        logger.info(f"Found {len(tests)} tests")
        
        if not tests:
            logger.error("No tests found!")
            return {'status': 'error', 'message': 'No tests found'}
        
        # 2. Categorize tests by resource requirements
        logger.info("Categorizing tests by resource requirements...")
        categorized_tests = self.distributor.categorize_tests(tests)
        
        for category, test_list in categorized_tests.items():
            logger.info(f"  {category}: {len(test_list)} tests")
        
        # 3. Calculate optimal distribution
        if optimize_cost:
            logger.info("Calculating cost-optimized distribution...")
            distribution = await self.cost_optimizer.optimize_distribution(
                categorized_tests
            )
        else:
            logger.info("Using standard distribution strategy...")
            distribution = self.distributor.calculate_distribution(
                categorized_tests,
                target_override=target
            )
        
        logger.info("Distribution plan:")
        for infra, test_list in distribution.items():
            logger.info(f"  {infra}: {len(test_list)} tests")
        
        # 4. Provision required infrastructure
        logger.info("Provisioning infrastructure...")
        await self.infra_manager.provision(distribution)
        
        # 5. Execute tests in parallel or serial
        logger.info(f"Executing tests ({'parallel' if parallel else 'serial'})...")
        
        if parallel:
            results = await self._execute_parallel(distribution)
        else:
            results = await self._execute_serial(distribution)
        
        # 6. Collect and aggregate results
        logger.info("Aggregating results...")
        aggregated_results = self._aggregate_results(results)
        
        # 7. Cleanup infrastructure
        logger.info("Cleaning up infrastructure...")
        await self.infra_manager.cleanup()
        
        # 8. Generate report
        self._generate_report(aggregated_results)
        
        logger.info("Test orchestration complete!")
        return aggregated_results
    
    async def _execute_parallel(self, distribution: Dict[str, List]) -> List[Dict]:
        """Execute tests in parallel across all infrastructure"""
        tasks = []
        
        for infrastructure, tests in distribution.items():
            if tests:
                task = self.infra_manager.execute_tests(
                    infrastructure,
                    tests,
                    parallel=True
                )
                tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if not isinstance(r, Exception)]
    
    async def _execute_serial(self, distribution: Dict[str, List]) -> List[Dict]:
        """Execute tests serially across infrastructure"""
        results = []
        
        for infrastructure, tests in distribution.items():
            if tests:
                result = await self.infra_manager.execute_tests(
                    infrastructure,
                    tests,
                    parallel=False
                )
                results.append(result)
        
        return results
    
    def _aggregate_results(self, results: List[Dict]) -> Dict:
        """Aggregate results from all infrastructure"""
        total_tests = 0
        passed = 0
        failed = 0
        skipped = 0
        total_duration = 0
        total_cost = 0.0
        
        infrastructure_breakdown = {}
        
        for result in results:
            infrastructure = result['infrastructure']
            total_tests += result['total']
            passed += result['passed']
            failed += result['failed']
            skipped += result['skipped']
            total_duration = max(total_duration, result['duration'])
            total_cost += result['cost']
            
            infrastructure_breakdown[infrastructure] = {
                'tests': result['total'],
                'passed': result['passed'],
                'failed': result['failed'],
                'duration': result['duration'],
                'cost': result['cost']
            }
        
        success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
        
        return {
            'status': 'success' if failed == 0 else 'failed',
            'total_tests': total_tests,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'success_rate': round(success_rate, 2),
            'total_duration_seconds': total_duration,
            'total_cost_usd': round(total_cost, 2),
            'infrastructure_breakdown': infrastructure_breakdown,
            'timestamp': asyncio.get_event_loop().time()
        }
    
    def _generate_report(self, results: Dict):
        """Generate human-readable test report"""
        print("\n" + "="*80)
        print("TEST EXECUTION REPORT")
        print("="*80)
        print(f"\nStatus: {results['status'].upper()}")
        print(f"Total Tests: {results['total_tests']}")
        print(f"Passed: {results['passed']} ({results['success_rate']}%)")
        print(f"Failed: {results['failed']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Duration: {results['total_duration_seconds']:.2f} seconds")
        print(f"Total Cost: ${results['total_cost_usd']}")
        
        print("\n" + "-"*80)
        print("INFRASTRUCTURE BREAKDOWN")
        print("-"*80)
        
        for infra, stats in results['infrastructure_breakdown'].items():
            print(f"\n{infra.upper()}:")
            print(f"  Tests: {stats['tests']}")
            print(f"  Passed: {stats['passed']}")
            print(f"  Failed: {stats['failed']}")
            print(f"  Duration: {stats['duration']:.2f}s")
            print(f"  Cost: ${stats['cost']:.2f}")
        
        print("\n" + "="*80 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Hybrid Test Infrastructure Orchestrator'
    )
    parser.add_argument(
        '--suite',
        choices=['all', 'unit', 'integration', 'e2e', 'performance'],
        default='all',
        help='Test suite to run'
    )
    parser.add_argument(
        '--target',
        choices=['cloud-spot', 'azure-aks', 'hci'],
        help='Force execution on specific infrastructure'
    )
    parser.add_argument(
        '--optimize-cost',
        action='store_true',
        help='Enable aggressive cost optimization'
    )
    parser.add_argument(
        '--serial',
        action='store_true',
        help='Execute tests serially instead of parallel'
    )
    parser.add_argument(
        '--config',
        default='config.yml',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    # Create orchestrator
    orchestrator = TestOrchestrator(config_path=args.config)
    
    # Run tests
    try:
        results = asyncio.run(
            orchestrator.run_tests(
                test_suite=args.suite,
                target=args.target,
                optimize_cost=args.optimize_cost,
                parallel=not args.serial
            )
        )
        
        # Exit with appropriate code
        sys.exit(0 if results['status'] == 'success' else 1)
        
    except KeyboardInterrupt:
        logger.info("Orchestration interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Orchestration failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
