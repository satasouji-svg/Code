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
        print("\n⚠️  NOTE: All costs are normalized/scaled for demonstration purposes.")
        print("         Results illustrate model behavior and solution quality.")
        
        self._print_solution_status()
        self._print_objective_breakdown()
        self._print_first_stage_decisions()
        self._print_risk_measures()
        self._print_equity_measures()
        self._print_utilization_metrics()
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
        """Print risk measures with context about stress-testing."""
        print(f"\n⚠️  Risk Measures:")
        print(f"   VaR at {self.config.optimization.cvar_alpha:.1%}: ${self.result.var_value:,.2f}")
        print(f"   CVaR at {self.config.optimization.cvar_alpha:.1%}: ${self.result.cvar_value:,.2f}")
        print(f"   Expected Cost: ${self.result.expected_cost:,.2f}")
        
        # Calculate risk premium (CVaR - Expected Cost)
        risk_premium = self.result.cvar_value - self.result.expected_cost
        if self.result.expected_cost > 0:
            risk_premium_pct = (risk_premium / self.result.expected_cost) * 100
            print(f"   Risk Premium: ${risk_premium:,.2f} ({risk_premium_pct:+.1f}%)")
            
            # Add context about risk premium magnitude
            if risk_premium_pct > 80:
                print(f"\n   ℹ️  Note: Large risk premium indicates heavy-tailed cost distribution")
                print(f"      This model uses stress-testing scenario generation with demand shocks")
                print(f"      capped at {self.config.scenario.max_sigma_deviation}σ to represent extreme events")
                print(f"      while maintaining computational tractability.")
    
    def _print_equity_measures(self):
        """Print equity measures with clear definitions."""
        print(f"\n⚖️  Equity Measures:")
        print(f"   (Definitions: Minimum = min over all (scenario, node) pairs;")
        print(f"                Average = probability-weighted mean over all (scenario, node) pairs)")
        
        print(f"\n   Minimum Demand Satisfaction: {self.result.min_satisfaction_ratio:.1%}")
        print(f"   Average Demand Satisfaction: {self.result.avg_satisfaction_ratio:.1%}")
        print(f"   Required Minimum: {self.config.optimization.min_demand_satisfaction:.1%}")
        
        if self.result.min_satisfaction_ratio >= self.config.optimization.min_demand_satisfaction:
            print(f"   ✅ Equity constraint satisfied")
        else:
            print(f"   ⚠️  Equity constraint violated")
        
        # Find and report worst-case equity violations
        worst_satisfaction = 1.0
        worst_node = None
        worst_scenario = None
        
        for scenario in self.scenarios:
            s = scenario.id
            for node in self.config.network.demand_nodes:
                demand = scenario.demand[node]
                unmet = self.result.scenario_unmet_demand[s][node]
                if demand > 0:
                    satisfaction = (demand - unmet) / demand
                    if satisfaction < worst_satisfaction:
                        worst_satisfaction = satisfaction
                        worst_node = node
                        worst_scenario = s
        
        if worst_node is not None:
            print(f"\n   Worst Case: Node {worst_node} in Scenario {worst_scenario} ({worst_satisfaction:.1%} satisfied)")
    
    def _print_utilization_metrics(self):
        """Print capacity utilization metrics with cost dominance analysis."""
        print(f"\n🏭 Capacity Utilization (Average across scenarios):")
        
        # Supplier utilization with cost dominance explanation
        if self.result.avg_supplier_utilization:
            print(f"\n   Supplier Capacity:")
            for supplier in sorted(self.result.avg_supplier_utilization.keys()):
                util = self.result.avg_supplier_utilization[supplier]
                print(f"      {supplier}: {util:.1f}%")
            
            # Add supplier cost dominance analysis
            print(f"\n   📊 Supplier Cost Analysis (explains utilization patterns):")
            self._print_supplier_cost_dominance()
        
        # DC utilization
        if self.result.avg_dc_utilization:
            print(f"\n   Distribution Center Storage:")
            for dc in sorted(self.result.avg_dc_utilization.keys()):
                util = self.result.avg_dc_utilization[dc]
                print(f"      {dc}: {util:.1f}%")
        
        # Top arc utilization
        if self.result.avg_arc_utilization:
            print(f"\n   Top Transport Arcs (>50% utilization):")
            sorted_arcs = sorted(
                self.result.avg_arc_utilization.items(),
                key=lambda x: x[1],
                reverse=True
            )
            high_util_arcs = [(arc, util) for arc, util in sorted_arcs if util > 50]
            if high_util_arcs:
                for arc, util in high_util_arcs[:10]:  # Show top 10
                    print(f"      {arc[0]} → {arc[1]}: {util:.1f}%")
            else:
                print(f"      None (all arcs below 50% utilization)")
        
        # Emergency procurement with economic analysis
        if self.result.scenarios_with_emergency > 0:
            print(f"\n   Emergency Actions:")
            print(f"      Scenarios requiring emergency procurement: {self.result.scenarios_with_emergency}/{len(self.scenarios)}")
            print(f"      Expected emergency procurement: {self.result.total_emergency_procurement:,.1f} units")
        else:
            print(f"\n   Emergency Actions:")
            print(f"      No emergency procurement triggered in any scenario")
            self._print_emergency_economics()
    
    def _print_supplier_cost_dominance(self):
        """Print supplier cost dominance analysis."""
        print(f"      Average unit costs from each supplier to DCs:")
        
        suppliers = self.config.network.suppliers
        dcs = self.config.network.distribution_centers
        
        # Calculate average cost for each supplier
        supplier_avg_costs = {}
        for supplier in suppliers:
            costs_to_dcs = []
            for dc in dcs:
                arc = (supplier, dc)
                if arc in self.config.network.arcs:
                    costs_to_dcs.append(self.config.network.arcs[arc]['cost'])
            if costs_to_dcs:
                supplier_avg_costs[supplier] = np.mean(costs_to_dcs)
        
        # Print sorted by cost
        for supplier in sorted(supplier_avg_costs.keys(), key=lambda s: supplier_avg_costs[s]):
            avg_cost = supplier_avg_costs[supplier]
            utilization = self.result.avg_supplier_utilization.get(supplier, 0.0)
            print(f"         {supplier}: ${avg_cost:.2f}/unit (avg to DCs), {utilization:.1f}% utilized")
        
        # Explain dominance based on actual utilization
        if self.result.avg_supplier_utilization:
            most_used = max(self.result.avg_supplier_utilization.keys(), 
                          key=lambda s: self.result.avg_supplier_utilization[s])
            most_used_util = self.result.avg_supplier_utilization[most_used]
            
            if most_used_util > 10:  # Only explain if significantly used
                print(f"\n      → {most_used} is primary supplier ({most_used_util:.1f}% utilization)")
                print(f"        Other suppliers serve as resilience backups for disruption scenarios")
                
                # Check if costs align with usage
                if most_used in supplier_avg_costs:
                    most_used_cost = supplier_avg_costs[most_used]
                    min_cost = min(supplier_avg_costs.values())
                    if most_used_cost > min_cost + 0.1:
                        print(f"        Note: {most_used} is not the cheapest supplier on average, but may have")
                        print(f"              advantages in specific routing paths or lower disruption exposure")
    
    def _print_emergency_economics(self):
        """Print economic explanation for why emergency procurement is not used."""
        emerg_cost = self.config.optimization.emergency_procurement_cost
        unmet_penalty = self.config.optimization.unmet_demand_penalty
        
        print(f"\n      Economic Trade-off Analysis:")
        print(f"         Emergency procurement cost: ${emerg_cost:.2f}/unit")
        print(f"         Unmet demand penalty: ${unmet_penalty:.2f}/unit")
        
        if emerg_cost < unmet_penalty:
            print(f"         → Emergency is cheaper; model prefers emergency over unmet")
            print(f"         → No emergency triggered suggests capacity constraints limit emergency sourcing")
        else:
            print(f"         → Unmet demand penalty is lower; model rationally prefers small unmet over emergency")
            print(f"         → This represents a policy choice: accept limited shortfalls rather than expensive emergency supply")
    
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
