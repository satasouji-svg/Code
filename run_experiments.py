"""
Comprehensive experiment runner for publishable results.

This module runs experiments across multiple instances and parameter configurations
to demonstrate model scalability, trade-offs, and robustness.
"""

import time
import pandas as pd
from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt
import seaborn as sns

from config import Config, OptimizationConfig
from scenario_generator import ScenarioGenerator
from optimization_model import TwoStageStochasticModel
from network_instances import get_all_instances, print_instance_summary
from parameter_sweep import ParameterSweep


class ExperimentRunner:
    """Runner for comprehensive publishable experiments."""
    
    def __init__(self, output_dir: str = 'results/experiments'):
        """
        Initialize experiment runner.
        
        Args:
            output_dir: Base directory for all experiment outputs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
        
    def run_scalability_experiments(self, n_scenarios: int = 100) -> pd.DataFrame:
        """
        Run experiments across all instances to demonstrate scalability.
        
        Tests: small, medium, large, stress instances
        
        Args:
            n_scenarios: Number of scenarios per instance
            
        Returns:
            DataFrame with results for each instance
        """
        print("\n" + "="*80)
        print("SCALABILITY EXPERIMENTS")
        print("="*80)
        print(f"Testing model scalability across 4 instance sizes")
        print(f"Scenarios per instance: {n_scenarios}")
        print("="*80 + "\n")
        
        instances = get_all_instances()
        results = []
        
        for name, network in instances.items():
            print(f"\n{'='*80}")
            print(f"INSTANCE: {name.upper()}")
            print(f"{'='*80}")
            print_instance_summary(name, network)
            
            # Create config
            config = Config(network=network)
            
            # Generate scenarios
            print(f"Generating {n_scenarios} scenarios...")
            gen = ScenarioGenerator(config)
            scenarios = gen.generate_scenarios()
            
            # Build model
            print("Building optimization model...")
            model = TwoStageStochasticModel(config, scenarios)
            model.build_model()
            
            # Get model statistics
            n_vars = len(model.model.variables())
            n_constraints = len(model.model.constraints)
            
            # Solve
            print("Solving...")
            start_time = time.time()
            result = model.solve()
            solve_time = time.time() - start_time
            
            if result.status == 'Optimal':
                # Calculate summary statistics
                total_inventory = sum(result.prepositioned_inventory.values())
                total_emergency = sum(sum(emerg.values()) for emerg in result.scenario_emergency_procurement.values())
                total_unmet = sum(sum(unmet.values()) for unmet in result.scenario_unmet_demand.values())
                scenarios_with_emergency = sum(1 for emerg in result.scenario_emergency_procurement.values() 
                                              if sum(emerg.values()) > 1e-6)
                
                # Calculate average utilization
                avg_supplier_util = sum(result.avg_supplier_utilization.values()) / len(result.avg_supplier_utilization) if result.avg_supplier_utilization else 0
                avg_dc_util = sum(result.avg_dc_utilization.values()) / len(result.avg_dc_utilization) if result.avg_dc_utilization else 0
                
                results.append({
                    'instance': name,
                    'suppliers': len(network.suppliers),
                    'dcs': len(network.distribution_centers),
                    'demand_nodes': len(network.demand_nodes),
                    'arcs': len(network.arcs),
                    'total_demand': sum(network.base_demand.values()),
                    'n_vars': n_vars,
                    'n_constraints': n_constraints,
                    'solve_time': solve_time,
                    'objective': result.objective_value,
                    'expected_cost': result.expected_cost,
                    'var': result.var_value,
                    'cvar': result.cvar_value,
                    'risk_premium_pct': ((result.cvar_value / result.expected_cost) - 1) * 100,
                    'total_inventory': total_inventory,
                    'total_emergency': total_emergency,
                    'total_unmet': total_unmet,
                    'scenarios_with_emergency': scenarios_with_emergency,
                    'min_satisfaction_pct': result.min_satisfaction_ratio * 100,
                    'avg_satisfaction_pct': result.avg_satisfaction_ratio * 100,
                    'avg_supplier_utilization': avg_supplier_util,
                    'avg_dc_utilization': avg_dc_util,
                    'status': result.status
                })
                
                print(f"\n✓ RESULTS:")
                print(f"   Objective: ${result.objective_value:,.2f}")
                print(f"   Variables: {n_vars}, Constraints: {n_constraints}")
                print(f"   Solve time: {solve_time:.3f}s")
                print(f"   CVaR: ${result.cvar_value:,.2f}")
                print(f"   Inventory: {total_inventory:.0f} units")
                print(f"   Emergency: {total_emergency:.1f} units in {scenarios_with_emergency} scenarios")
                print(f"   Unmet: {total_unmet:.1f} units")
                print(f"   Min satisfaction: {result.min_satisfaction_ratio*100:.1f}%")
            else:
                print(f"\n✗ FAILED: {result.status}")
                results.append({
                    'instance': name,
                    'status': result.status,
                })
        
        df = pd.DataFrame(results)
        
        # Save results
        output_file = self.output_dir / 'scalability_results.csv'
        df.to_csv(output_file, index=False)
        print(f"\n✓ Scalability results saved to {output_file}")
        
        # Generate comparison plots
        self._plot_scalability_results(df)
        
        # Generate summary table
        self._print_scalability_summary(df)
        
        return df
    
    def run_parameter_sweeps_all_instances(self, n_scenarios: int = 100):
        """
        Run parameter sweeps on all instances.
        
        Args:
            n_scenarios: Number of scenarios per instance
        """
        print("\n" + "="*80)
        print("PARAMETER SWEEP EXPERIMENTS (ALL INSTANCES)")
        print("="*80)
        
        instance_names = ['small', 'medium', 'stress']  # Skip 'large' for time
        
        for instance_name in instance_names:
            print(f"\n{'='*80}")
            print(f"Running sweeps for instance: {instance_name.upper()}")
            print(f"{'='*80}")
            
            sweep = ParameterSweep(instance_name, n_scenarios)
            
            # Risk weight sweep
            print(f"\n--- Risk Weight Sweep ---")
            sweep.run_risk_weight_sweep()
            
            # CVaR alpha sweep
            print(f"\n--- CVaR Alpha Sweep ---")
            sweep.run_cvar_alpha_sweep()
    
    def run_stress_test_analysis(self, n_scenarios: int = 150):
        """
        Deep dive analysis on stress instance to demonstrate binding constraints.
        
        Args:
            n_scenarios: Number of scenarios (more for stress testing)
        """
        print("\n" + "="*80)
        print("STRESS TEST ANALYSIS")
        print("="*80)
        print(f"Deep analysis of stress instance with {n_scenarios} scenarios")
        print(f"Goal: Demonstrate emergency triggers and binding equity constraints")
        print("="*80 + "\n")
        
        # Test with different equity requirements
        equity_values = [0.75, 0.85, 0.90, 0.95]
        results = []
        
        network = get_all_instances()['stress']
        
        for equity_min in equity_values:
            print(f"\n--- Testing min_satisfaction = {equity_min:.0%} ---")
            
            config = Config(
                network=network,
                optimization=OptimizationConfig(
                    min_satisfaction=equity_min,
                    expected_cost_weight=0.5,
                    cvar_weight=0.5
                )
            )
            
            gen = ScenarioGenerator(config)
            scenarios = gen.generate_scenarios()
            
            model = TwoStageStochasticModel(config, scenarios)
            model.build_model()
            result = model.solve()
            
            if result.status == 'Optimal':
                total_emergency = sum(sum(emerg.values()) for emerg in result.scenario_emergency_procurement.values())
                total_unmet = sum(sum(unmet.values()) for unmet in result.scenario_unmet_demand.values())
                scenarios_with_emergency = sum(1 for emerg in result.scenario_emergency_procurement.values() 
                                              if sum(emerg.values()) > 1e-6)
                
                results.append({
                    'min_satisfaction_req': equity_min * 100,
                    'min_satisfaction_actual': result.min_satisfaction_ratio * 100,
                    'objective': result.objective_value,
                    'cvar': result.cvar_value,
                    'total_inventory': sum(result.prepositioned_inventory.values()),
                    'total_emergency': total_emergency,
                    'scenarios_with_emergency': scenarios_with_emergency,
                    'total_unmet': total_unmet,
                    'status': result.status
                })
                
                print(f"   ✓ Objective: ${result.objective_value:,.2f}")
                print(f"   ✓ Emergency: {total_emergency:.1f} units in {scenarios_with_emergency} scenarios")
                print(f"   ✓ Unmet: {total_unmet:.1f} units")
                print(f"   ✓ Min satisfaction: {result.min_satisfaction_ratio*100:.1f}%")
                
                # Check if equity constraint is binding
                gap = result.min_satisfaction_ratio - equity_min
                if abs(gap) < 0.01:
                    print(f"   ⚠️  EQUITY CONSTRAINT IS BINDING (gap={gap:.4f})")
        
        df = pd.DataFrame(results)
        output_file = self.output_dir / 'stress_test_equity_analysis.csv'
        df.to_csv(output_file, index=False)
        print(f"\n✓ Stress test results saved to {output_file}")
        
        return df
    
    def _plot_scalability_results(self, df: pd.DataFrame):
        """Generate scalability comparison plots."""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Model Scalability Across Instance Sizes', fontsize=16, fontweight='bold')
        
        # Sort by network size
        df = df.sort_values('total_demand')
        
        # 1. Problem size
        ax = axes[0, 0]
        x = range(len(df))
        width = 0.35
        ax.bar([i - width/2 for i in x], df['n_vars'], width, label='Variables', alpha=0.7)
        ax.bar([i + width/2 for i in x], df['n_constraints'], width, label='Constraints', alpha=0.7)
        ax.set_xticks(x)
        ax.set_xticklabels(df['instance'], rotation=45)
        ax.set_ylabel('Count', fontsize=11)
        ax.set_title('Problem Size', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # 2. Solve time
        ax = axes[0, 1]
        ax.bar(df['instance'], df['solve_time'], alpha=0.7, color='orange')
        ax.set_ylabel('Time (seconds)', fontsize=11)
        ax.set_title('Solve Time', fontsize=12)
        ax.set_xticklabels(df['instance'], rotation=45)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 3. Objective value
        ax = axes[0, 2]
        ax.bar(df['instance'], df['objective'], alpha=0.7, color='green')
        ax.set_ylabel('Cost ($1000 CAD)', fontsize=11)
        ax.set_title('Total Objective', fontsize=12)
        ax.set_xticklabels(df['instance'], rotation=45)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 4. Emergency procurement
        ax = axes[1, 0]
        ax.bar(df['instance'], df['total_emergency'], alpha=0.7, color='purple')
        ax.set_ylabel('Units', fontsize=11)
        ax.set_title('Emergency Procurement', fontsize=12)
        ax.set_xticklabels(df['instance'], rotation=45)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 5. Unmet demand
        ax = axes[1, 1]
        ax.bar(df['instance'], df['total_unmet'], alpha=0.7, color='red')
        ax.set_ylabel('Units', fontsize=11)
        ax.set_title('Unmet Demand', fontsize=12)
        ax.set_xticklabels(df['instance'], rotation=45)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 6. Satisfaction rate
        ax = axes[1, 2]
        ax.bar(df['instance'], df['min_satisfaction_pct'], alpha=0.7, color='blue')
        ax.set_ylabel('Percentage (%)', fontsize=11)
        ax.set_title('Min Demand Satisfaction', fontsize=12)
        ax.set_xticklabels(df['instance'], rotation=45)
        ax.axhline(y=75, color='r', linestyle='--', label='Required (75%)')
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        output_file = self.output_dir / 'scalability_comparison.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Scalability plot saved to {output_file}")
        plt.close()
    
    def _print_scalability_summary(self, df: pd.DataFrame):
        """Print formatted scalability summary table."""
        print("\n" + "="*80)
        print("SCALABILITY SUMMARY TABLE")
        print("="*80)
        print(f"{'Instance':<10} {'Nodes':<12} {'Vars':<8} {'Constrs':<8} {'Time(s)':<10} {'Emergency':<12} {'Unmet':<10}")
        print("-"*80)
        for _, row in df.iterrows():
            nodes = f"{row['suppliers']}-{row['dcs']}-{row['demand_nodes']}"
            print(f"{row['instance']:<10} {nodes:<12} {row['n_vars']:<8.0f} {row['n_constraints']:<8.0f} "
                  f"{row['solve_time']:<10.3f} {row['total_emergency']:<12.1f} {row['total_unmet']:<10.1f}")
        print("="*80 + "\n")


def run_all_experiments():
    """Run complete experiment suite for publication."""
    runner = ExperimentRunner()
    
    print("\n" + "="*80)
    print("COMPREHENSIVE EXPERIMENT SUITE FOR PUBLICATION")
    print("="*80)
    print("This will run:")
    print("  1. Scalability experiments (4 instances)")
    print("  2. Parameter sweeps (3 instances × 2 sweeps)")
    print("  3. Stress test analysis (binding constraints)")
    print("="*80 + "\n")
    
    input("Press Enter to start experiments (or Ctrl+C to cancel)...")
    
    # 1. Scalability experiments
    print("\n\n" + "█"*80)
    print("█ EXPERIMENT 1: SCALABILITY")
    print("█"*80)
    df_scalability = runner.run_scalability_experiments(n_scenarios=100)
    
    # 2. Parameter sweeps
    print("\n\n" + "█"*80)
    print("█ EXPERIMENT 2: PARAMETER SWEEPS")
    print("█"*80)
    runner.run_parameter_sweeps_all_instances(n_scenarios=100)
    
    # 3. Stress test analysis
    print("\n\n" + "█"*80)
    print("█ EXPERIMENT 3: STRESS TEST ANALYSIS")
    print("█"*80)
    df_stress = runner.run_stress_test_analysis(n_scenarios=150)
    
    print("\n\n" + "="*80)
    print("✓ ALL EXPERIMENTS COMPLETE")
    print("="*80)
    print(f"Results saved to: {runner.output_dir}")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_all_experiments()
