"""
Reporting module for optimization results.

This module provides comprehensive reporting of optimization results including
summary statistics, scenario analysis, and detailed breakdowns.
"""

import numpy as np
from typing import List
from config import Config
from scenario_generator import Scenario
from optimization_model import OptimizationResult


class Reporter:
    """Generates comprehensive reports from optimization results."""
    
    def __init__(self, config: Config, scenarios: List[Scenario], result: OptimizationResult):
        """
        Initialize reporter.
        
        Args:
            config: Configuration object
            scenarios: List of scenarios
            result: Optimization result
        """
        self.config = config
        self.scenarios = scenarios
        self.result = result
    
    def print_summary(self):
        """Print a comprehensive summary of the optimization results."""
        print("\n" + "="*80)
        print("OPTIMIZATION SUMMARY")
        print("="*80)
        
        self._print_solution_status()
        self._print_objective_breakdown()
        self._print_first_stage_decisions()
        self._print_risk_measures()
        self._print_equity_measures()
        self._print_scenario_statistics()
        
        print("="*80 + "\n")
    
    def _print_solution_status(self):
        """Print solution status information."""
        print(f"\n📊 Solution Status:")
        print(f"   Status: {self.result.status}")
        print(f"   Solve Time: {self.result.solve_time:.2f} seconds")
        print(f"   Total Objective: ${self.result.objective_value:,.2f}")
    
    def _print_objective_breakdown(self):
        """Print breakdown of objective function components."""
        print(f"\n💰 Objective Breakdown:")
        
        # First stage costs
        first_stage_cost = sum(
            inv * self.config.network.facilities[dc]['holding_cost']
            for dc, inv in self.result.prepositioned_inventory.items()
        )
        print(f"   First Stage (Inventory): ${first_stage_cost:,.2f}")
        
        # Second stage costs
        print(f"   Expected Cost E[Q]: ${self.result.expected_cost:,.2f}")
        print(f"   CVaR_{self.config.optimization.cvar_alpha}: ${self.result.cvar_value:,.2f}")
        
        # Risk-adjusted second stage
        w_exp = self.config.optimization.expectation_weight
        w_cvar = self.config.optimization.cvar_weight
        risk_adjusted = w_exp * self.result.expected_cost + w_cvar * self.result.cvar_value
        print(f"   Risk-Adjusted Cost: ${risk_adjusted:,.2f}")
        print(f"      ({w_exp:.1%} × E[Q] + {w_cvar:.1%} × CVaR)")
    
    def _print_first_stage_decisions(self):
        """Print first stage (preparedness) decisions."""
        print(f"\n📦 First Stage Decisions (Prepositioned Inventory):")
        
        total_inventory = 0
        for dc, inventory in sorted(self.result.prepositioned_inventory.items()):
            storage_cap = self.config.network.facilities[dc]['storage_capacity']
            utilization = (inventory / storage_cap * 100) if storage_cap > 0 else 0
            print(f"   {dc}: {inventory:,.1f} units ({utilization:.1f}% of capacity)")
            total_inventory += inventory
        
        print(f"   Total: {total_inventory:,.1f} units")
    
    def _print_risk_measures(self):
        """Print risk measures."""
        print(f"\n⚠️  Risk Measures:")
        print(f"   VaR at {self.config.optimization.cvar_alpha:.1%}: ${self.result.var_value:,.2f}")
        print(f"   CVaR at {self.config.optimization.cvar_alpha:.1%}: ${self.result.cvar_value:,.2f}")
        print(f"   Expected Cost: ${self.result.expected_cost:,.2f}")
        
        # Calculate risk premium (CVaR - Expected Cost)
        risk_premium = self.result.cvar_value - self.result.expected_cost
        if self.result.expected_cost > 0:
            risk_premium_pct = (risk_premium / self.result.expected_cost) * 100
            print(f"   Risk Premium: ${risk_premium:,.2f} ({risk_premium_pct:+.1f}%)")
    
    def _print_equity_measures(self):
        """Print equity measures."""
        print(f"\n⚖️  Equity Measures:")
        print(f"   Minimum Demand Satisfaction: {self.result.min_satisfaction_ratio:.1%}")
        print(f"   Average Demand Satisfaction: {self.result.avg_satisfaction_ratio:.1%}")
        print(f"   Required Minimum: {self.config.optimization.min_demand_satisfaction:.1%}")
        
        if self.result.min_satisfaction_ratio >= self.config.optimization.min_demand_satisfaction:
            print(f"   ✅ Equity constraint satisfied")
        else:
            print(f"   ⚠️  Equity constraint violated")
    
    def _print_scenario_statistics(self):
        """Print scenario-level statistics."""
        print(f"\n📈 Scenario Statistics:")
        
        # Scenario costs
        costs = list(self.result.scenario_costs.values())
        print(f"   Number of Scenarios: {len(self.scenarios)}")
        print(f"   Cost Range: ${min(costs):,.2f} - ${max(costs):,.2f}")
        print(f"   Mean Cost: ${np.mean(costs):,.2f}")
        print(f"   Std Dev: ${np.std(costs):,.2f}")
        
        # Unmet demand statistics
        total_unmet_by_scenario = []
        for s in range(len(self.scenarios)):
            total_unmet = sum(self.result.scenario_unmet_demand[s].values())
            total_unmet_by_scenario.append(total_unmet)
        
        print(f"\n   Unmet Demand Statistics:")
        print(f"   Total Unmet (across scenarios): {sum(total_unmet_by_scenario):,.1f} units")
        print(f"   Mean Unmet per Scenario: {np.mean(total_unmet_by_scenario):,.1f} units")
        print(f"   Max Unmet in Scenario: {max(total_unmet_by_scenario):,.1f} units")
        
        # Emergency procurement statistics
        total_emergency_by_scenario = []
        for s in range(len(self.scenarios)):
            total_emergency = sum(self.result.scenario_emergency_procurement[s].values())
            total_emergency_by_scenario.append(total_emergency)
        
        if sum(total_emergency_by_scenario) > 0:
            print(f"\n   Emergency Procurement:")
            print(f"   Total Emergency (across scenarios): {sum(total_emergency_by_scenario):,.1f} units")
            print(f"   Scenarios with Emergency: {sum(1 for x in total_emergency_by_scenario if x > 0)}")
    
    def generate_detailed_report(self) -> str:
        """
        Generate a detailed text report.
        
        Returns:
            String containing detailed report
        """
        lines = []
        lines.append("="*80)
        lines.append("DETAILED OPTIMIZATION REPORT")
        lines.append("="*80)
        lines.append("")
        
        # Configuration summary
        lines.append("CONFIGURATION")
        lines.append("-"*80)
        lines.append(f"Network: {len(self.config.network.suppliers)} suppliers, "
                    f"{len(self.config.network.distribution_centers)} DCs, "
                    f"{len(self.config.network.demand_nodes)} demand nodes")
        lines.append(f"Scenarios: {len(self.scenarios)}")
        lines.append(f"CVaR Alpha: {self.config.optimization.cvar_alpha}")
        lines.append(f"Min Demand Satisfaction: {self.config.optimization.min_demand_satisfaction}")
        lines.append("")
        
        # Solution status
        lines.append("SOLUTION")
        lines.append("-"*80)
        lines.append(f"Status: {self.result.status}")
        lines.append(f"Objective: ${self.result.objective_value:,.2f}")
        lines.append(f"Solve Time: {self.result.solve_time:.2f}s")
        lines.append("")
        
        # First stage decisions
        lines.append("FIRST STAGE DECISIONS")
        lines.append("-"*80)
        for dc, inv in sorted(self.result.prepositioned_inventory.items()):
            lines.append(f"{dc}: {inv:,.2f} units")
        lines.append("")
        
        # Scenario details
        lines.append("SCENARIO DETAILS")
        lines.append("-"*80)
        
        for scenario in self.scenarios[:5]:  # Show first 5 scenarios
            s = scenario.id
            lines.append(f"\nScenario {s} (probability: {scenario.probability:.3f})")
            lines.append(f"  Cost: ${self.result.scenario_costs[s]:,.2f}")
            
            # Demand and satisfaction
            lines.append(f"  Demand Satisfaction:")
            for node in self.config.network.demand_nodes:
                demand = scenario.demand[node]
                unmet = self.result.scenario_unmet_demand[s][node]
                satisfied = demand - unmet
                ratio = satisfied / demand if demand > 0 else 1.0
                lines.append(f"    {node}: {satisfied:,.1f}/{demand:,.1f} ({ratio:.1%})")
        
        if len(self.scenarios) > 5:
            lines.append(f"\n... and {len(self.scenarios) - 5} more scenarios")
        
        lines.append("")
        lines.append("="*80)
        
        return "\n".join(lines)
    
    def save_report(self, filename: str):
        """
        Save detailed report to file.
        
        Args:
            filename: Output filename
        """
        report = self.generate_detailed_report()
        with open(filename, 'w') as f:
            f.write(report)
        print(f"📄 Report saved to {filename}")


def print_summary(config: Config, scenarios: List[Scenario], result: OptimizationResult):
    """
    Convenience function to print summary report.
    
    Args:
        config: Configuration object
        scenarios: List of scenarios
        result: Optimization result
    """
    reporter = Reporter(config, scenarios, result)
    reporter.print_summary()
