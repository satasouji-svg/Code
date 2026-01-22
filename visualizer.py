"""
Visualization module for optimization results.

This module creates comprehensive visualizations including network diagrams,
scenario analysis, and sensitivity analysis plots.
"""

import matplotlib.pyplot as plt
import numpy as np
from typing import List, Optional
import os
from config import Config
from scenario_generator import Scenario
from optimization_model import OptimizationResult


class Visualizer:
    """Creates visualizations for optimization results."""
    
    def __init__(self, config: Config, scenarios: List[Scenario], result: OptimizationResult):
        """
        Initialize visualizer.
        
        Args:
            config: Configuration object
            scenarios: List of scenarios
            result: Optimization result
        """
        self.config = config
        self.scenarios = scenarios
        self.result = result
        
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid' if 'seaborn-v0_8-darkgrid' in plt.style.available else 'default')
    
    def create_all_visualizations(self, output_dir: str = "results"):
        """
        Create all visualizations and save to directory.
        
        Args:
            output_dir: Directory to save plots
        """
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"📊 Creating visualizations...")
        
        self.plot_scenario_costs(os.path.join(output_dir, "scenario_costs.png"))
        self.plot_demand_satisfaction(os.path.join(output_dir, "demand_satisfaction.png"))
        self.plot_inventory_allocation(os.path.join(output_dir, "inventory_allocation.png"))
        self.plot_risk_analysis(os.path.join(output_dir, "risk_analysis.png"))
        
        print(f"✅ Visualizations saved to {output_dir}/")
    
    def plot_scenario_costs(self, filename: str):
        """
        Plot scenario costs with CVaR visualization.
        
        Args:
            filename: Output filename
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Extract scenario costs
        scenario_ids = sorted(self.result.scenario_costs.keys())
        costs = [self.result.scenario_costs[s] for s in scenario_ids]
        
        # Sort for better visualization
        sorted_indices = np.argsort(costs)
        sorted_costs = [costs[i] for i in sorted_indices]
        sorted_ids = [scenario_ids[i] for i in sorted_indices]
        
        # Plot bars
        bars = ax.bar(range(len(sorted_ids)), sorted_costs, alpha=0.7, color='steelblue')
        
        # Highlight scenarios above VaR
        var_value = self.result.var_value
        cvar_alpha = self.config.optimization.cvar_alpha
        var_threshold_idx = int(len(sorted_costs) * cvar_alpha)
        
        for i in range(var_threshold_idx, len(bars)):
            bars[i].set_color('coral')
            bars[i].set_alpha(0.9)
        
        # Add reference lines
        ax.axhline(y=self.result.expected_cost, color='green', linestyle='--', 
                   linewidth=2, label=f'Expected Cost: ${self.result.expected_cost:,.0f}')
        ax.axhline(y=var_value, color='orange', linestyle='--', 
                   linewidth=2, label=f'VaR ({cvar_alpha:.0%}): ${var_value:,.0f}')
        ax.axhline(y=self.result.cvar_value, color='red', linestyle='--', 
                   linewidth=2, label=f'CVaR ({cvar_alpha:.0%}): ${self.result.cvar_value:,.0f}')
        
        ax.set_xlabel('Scenario (sorted by cost)', fontsize=12)
        ax.set_ylabel('Total Cost ($)', fontsize=12)
        ax.set_title('Scenario Cost Distribution with Risk Measures', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_demand_satisfaction(self, filename: str):
        """
        Plot demand satisfaction rates across scenarios.
        
        Args:
            filename: Output filename
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Calculate satisfaction rates
        demand_nodes = self.config.network.demand_nodes
        satisfaction_by_node = {node: [] for node in demand_nodes}
        
        for scenario in self.scenarios:
            s = scenario.id
            for node in demand_nodes:
                demand = scenario.demand[node]
                unmet = self.result.scenario_unmet_demand[s][node]
                satisfied = demand - unmet
                ratio = satisfied / demand if demand > 0 else 1.0
                satisfaction_by_node[node].append(ratio * 100)
        
        # Plot 1: Box plot of satisfaction rates by node
        data = [satisfaction_by_node[node] for node in demand_nodes]
        bp = ax1.boxplot(data, labels=demand_nodes, patch_artist=True)
        
        for patch in bp['boxes']:
            patch.set_facecolor('lightblue')
            patch.set_alpha(0.7)
        
        ax1.axhline(y=self.config.optimization.min_demand_satisfaction * 100, 
                    color='red', linestyle='--', linewidth=2, 
                    label=f'Min Required: {self.config.optimization.min_demand_satisfaction:.0%}')
        ax1.set_ylabel('Demand Satisfaction Rate (%)', fontsize=12)
        ax1.set_title('Demand Satisfaction by Node', fontsize=14, fontweight='bold')
        ax1.legend(loc='lower left', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim([0, 105])
        
        # Plot 2: Heatmap of satisfaction rates
        satisfaction_matrix = np.zeros((len(self.scenarios), len(demand_nodes)))
        for i, scenario in enumerate(self.scenarios):
            s = scenario.id
            for j, node in enumerate(demand_nodes):
                satisfaction_matrix[i, j] = satisfaction_by_node[node][i]
        
        im = ax2.imshow(satisfaction_matrix, aspect='auto', cmap='RdYlGn', vmin=0, vmax=100)
        ax2.set_xlabel('Demand Node', fontsize=12)
        ax2.set_ylabel('Scenario', fontsize=12)
        ax2.set_title('Demand Satisfaction Heatmap (%)', fontsize=14, fontweight='bold')
        ax2.set_xticks(range(len(demand_nodes)))
        ax2.set_xticklabels(demand_nodes)
        ax2.set_yticks(range(0, len(self.scenarios), max(1, len(self.scenarios)//10)))
        
        cbar = plt.colorbar(im, ax=ax2)
        cbar.set_label('Satisfaction %', fontsize=10)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_inventory_allocation(self, filename: str):
        """
        Plot prepositioned inventory allocation.
        
        Args:
            filename: Output filename
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        dcs = sorted(self.result.prepositioned_inventory.keys())
        inventories = [self.result.prepositioned_inventory[dc] for dc in dcs]
        capacities = [self.config.network.facilities[dc]['storage_capacity'] for dc in dcs]
        
        x = np.arange(len(dcs))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, inventories, width, label='Prepositioned', 
                       color='steelblue', alpha=0.8)
        bars2 = ax.bar(x + width/2, capacities, width, label='Capacity', 
                       color='lightgray', alpha=0.6)
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.0f}',
                   ha='center', va='bottom', fontsize=10)
        
        # Calculate utilization
        for i, dc in enumerate(dcs):
            utilization = (inventories[i] / capacities[i]) * 100
            ax.text(i, capacities[i] + max(capacities)*0.02, 
                   f'{utilization:.1f}%',
                   ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.set_xlabel('Distribution Center', fontsize=12)
        ax.set_ylabel('Inventory Units', fontsize=12)
        ax.set_title('Prepositioned Inventory Allocation', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(dcs)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
    
    def plot_risk_analysis(self, filename: str):
        """
        Plot risk analysis including cost distribution and risk measures.
        
        Args:
            filename: Output filename
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        
        # Get costs
        costs = [self.result.scenario_costs[s] for s in sorted(self.result.scenario_costs.keys())]
        
        # Plot 1: Histogram of costs
        ax1.hist(costs, bins=20, alpha=0.7, color='steelblue', edgecolor='black')
        ax1.axvline(x=self.result.expected_cost, color='green', linestyle='--', 
                    linewidth=2, label='Expected Cost')
        ax1.axvline(x=self.result.var_value, color='orange', linestyle='--', 
                    linewidth=2, label='VaR')
        ax1.axvline(x=self.result.cvar_value, color='red', linestyle='--', 
                    linewidth=2, label='CVaR')
        ax1.set_xlabel('Cost ($)', fontsize=11)
        ax1.set_ylabel('Frequency', fontsize=11)
        ax1.set_title('Cost Distribution', fontsize=12, fontweight='bold')
        ax1.legend(fontsize=9)
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Cumulative distribution
        sorted_costs = np.sort(costs)
        cumulative = np.arange(1, len(sorted_costs) + 1) / len(sorted_costs)
        ax2.plot(sorted_costs, cumulative * 100, linewidth=2, color='steelblue')
        ax2.axvline(x=self.result.var_value, color='orange', linestyle='--', 
                    linewidth=2, label=f'VaR ({self.config.optimization.cvar_alpha:.0%})')
        ax2.axhline(y=self.config.optimization.cvar_alpha * 100, color='orange', 
                    linestyle=':', alpha=0.5)
        ax2.set_xlabel('Cost ($)', fontsize=11)
        ax2.set_ylabel('Cumulative Probability (%)', fontsize=11)
        ax2.set_title('Cumulative Distribution Function', fontsize=12, fontweight='bold')
        ax2.legend(fontsize=9)
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Cost components breakdown
        # Calculate average component costs
        transport_costs = []
        emergency_costs = []
        penalty_costs = []
        
        for scenario in self.scenarios:
            s = scenario.id
            
            # Transportation
            transport = sum(
                self.result.scenario_flows[s].get(arc, 0) * self.config.network.arcs[arc]['cost']
                for arc in self.config.network.arcs.keys()
            )
            transport_costs.append(transport)
            
            # Emergency procurement
            emergency = sum(
                self.result.scenario_emergency_procurement[s].get(sup, 0) 
                * self.config.optimization.emergency_procurement_cost
                for sup in self.config.network.suppliers
            )
            emergency_costs.append(emergency)
            
            # Penalties
            penalty = sum(
                self.result.scenario_unmet_demand[s][node] 
                * self.config.optimization.unmet_demand_penalty
                for node in self.config.network.demand_nodes
            )
            penalty_costs.append(penalty)
        
        avg_transport = np.mean(transport_costs)
        avg_emergency = np.mean(emergency_costs)
        avg_penalty = np.mean(penalty_costs)
        
        components = ['Transportation', 'Emergency\nProcurement', 'Unmet\nDemand']
        values = [avg_transport, avg_emergency, avg_penalty]
        colors = ['steelblue', 'orange', 'coral']
        
        wedges, texts, autotexts = ax3.pie(values, labels=components, autopct='%1.1f%%',
                                            colors=colors, startangle=90)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        ax3.set_title('Average Cost Breakdown', fontsize=12, fontweight='bold')
        
        # Plot 4: Scenario comparison
        n_scenarios_to_show = min(10, len(self.scenarios))
        scenario_ids = list(range(n_scenarios_to_show))
        scenario_costs_subset = [costs[s] for s in scenario_ids]
        
        bars = ax4.bar(scenario_ids, scenario_costs_subset, alpha=0.7, color='steelblue')
        ax4.axhline(y=self.result.expected_cost, color='green', linestyle='--', 
                    linewidth=2, label='Expected')
        ax4.set_xlabel('Scenario ID', fontsize=11)
        ax4.set_ylabel('Cost ($)', fontsize=11)
        ax4.set_title(f'Cost by Scenario (first {n_scenarios_to_show})', fontsize=12, fontweight='bold')
        ax4.legend(fontsize=9)
        ax4.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()


def create_visualizations(config: Config, scenarios: List[Scenario], 
                         result: OptimizationResult, output_dir: str = "results"):
    """
    Convenience function to create all visualizations.
    
    Args:
        config: Configuration object
        scenarios: List of scenarios
        result: Optimization result
        output_dir: Directory to save plots
    """
    visualizer = Visualizer(config, scenarios, result)
    visualizer.create_all_visualizations(output_dir)
