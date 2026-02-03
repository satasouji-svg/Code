"""
Parameter sweep framework for systematic experiments.

This module provides functionality to systematically vary optimization parameters
(risk weight λ, CVaR level α) and analyze their impact on solution characteristics.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple
from pathlib import Path
import time

from config import Config, OptimizationConfig
from scenario_generator import ScenarioGenerator
from optimization_model import TwoStageStochasticModel
from network_instances import get_instance_by_name


class ParameterSweep:
    """Framework for systematic parameter sweep experiments."""
    
    def __init__(self, instance_name: str = 'small', n_scenarios: int = 100):
        """
        Initialize parameter sweep.
        
        Args:
            instance_name: Name of network instance to use
            n_scenarios: Number of scenarios for stochastic optimization
        """
        self.instance_name = instance_name
        self.n_scenarios = n_scenarios
        self.results = []
        
    def run_risk_weight_sweep(self, 
                              lambda_values: List[float] = None,
                              alpha: float = 0.90,
                              output_dir: str = 'results/sweeps') -> pd.DataFrame:
        """
        Sweep over risk weight λ (CVaR weight in objective).
        
        Args:
            lambda_values: List of λ values to test (default: [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
            alpha: CVaR confidence level (fixed)
            output_dir: Directory for saving results
            
        Returns:
            DataFrame with results for each λ value
        """
        if lambda_values is None:
            lambda_values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        
        print(f"\n{'='*80}")
        print(f"RISK WEIGHT SWEEP: Instance={self.instance_name}, α={alpha}, Scenarios={self.n_scenarios}")
        print(f"{'='*80}")
        print(f"Testing λ values: {lambda_values}")
        print(f"{'='*80}\n")
        
        results = []
        
        for i, lambda_val in enumerate(lambda_values):
            print(f"\n[{i+1}/{len(lambda_values)}] Running λ = {lambda_val:.2f}...")
            
            # Create config with this lambda value
            network = get_instance_by_name(self.instance_name)
            config = Config(
                network=network,
                optimization=OptimizationConfig(
                    expected_cost_weight=1.0 - lambda_val,
                    cvar_weight=lambda_val,
                    cvar_alpha=alpha
                )
            )
            
            # Generate scenarios
            gen = ScenarioGenerator(config)
            scenarios = gen.generate_scenarios()
            
            # Build and solve model
            model = TwoStageStochasticModel(config, scenarios)
            model.build_model()
            result = model.solve()
            
            if result.status == 'Optimal':
                # Extract key metrics
                total_inventory = sum(result.prepositioned_inventory.values())
                total_emergency = sum(sum(emerg.values()) for emerg in result.scenario_emergency_procurement.values())
                total_unmet = sum(sum(unmet.values()) for unmet in result.scenario_unmet_demand.values())
                scenarios_with_emergency = sum(1 for emerg in result.scenario_emergency_procurement.values() 
                                              if sum(emerg.values()) > 1e-6)
                
                results.append({
                    'lambda': lambda_val,
                    'alpha': alpha,
                    'objective': result.objective_value,
                    'expected_cost': result.expected_cost,
                    'var': result.var_value,
                    'cvar': result.cvar_value,
                    'risk_premium_pct': ((result.cvar_value / result.expected_cost) - 1) * 100 if result.expected_cost > 0 else 0,
                    'total_inventory': total_inventory,
                    'total_emergency': total_emergency,
                    'total_unmet': total_unmet,
                    'scenarios_with_emergency': scenarios_with_emergency,
                    'min_satisfaction_pct': result.min_satisfaction_ratio * 100,
                    'avg_satisfaction_pct': result.avg_satisfaction_ratio * 100,
                    'solve_time': result.solve_time,
                    'status': result.status
                })
                
                print(f"   ✓ Objective: ${result.objective_value:,.2f}")
                print(f"   ✓ CVaR: ${result.cvar_value:,.2f}")
                print(f"   ✓ Inventory: {total_inventory:.0f} units")
                print(f"   ✓ Emergency: {total_emergency:.1f} units ({scenarios_with_emergency} scenarios)")
                print(f"   ✓ Unmet: {total_unmet:.1f} units")
            else:
                print(f"   ✗ Failed with status: {result.status}")
                results.append({
                    'lambda': lambda_val,
                    'alpha': alpha,
                    'status': result.status,
                    'objective': None,
                })
        
        df = pd.DataFrame(results)
        
        # Save results
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir) / f'risk_weight_sweep_{self.instance_name}_alpha{alpha:.2f}.csv'
        df.to_csv(output_file, index=False)
        print(f"\n✓ Results saved to {output_file}")
        
        # Generate plots
        self._plot_risk_weight_results(df, lambda_values, alpha, output_dir)
        
        return df
    
    def run_cvar_alpha_sweep(self,
                             alpha_values: List[float] = None,
                             lambda_val: float = 0.5,
                             output_dir: str = 'results/sweeps') -> pd.DataFrame:
        """
        Sweep over CVaR confidence level α.
        
        Args:
            alpha_values: List of α values to test (default: [0.80, 0.85, 0.90, 0.95])
            lambda_val: Risk weight (fixed)
            output_dir: Directory for saving results
            
        Returns:
            DataFrame with results for each α value
        """
        if alpha_values is None:
            alpha_values = [0.80, 0.85, 0.90, 0.95]
        
        print(f"\n{'='*80}")
        print(f"CVAR ALPHA SWEEP: Instance={self.instance_name}, λ={lambda_val}, Scenarios={self.n_scenarios}")
        print(f"{'='*80}")
        print(f"Testing α values: {alpha_values}")
        print(f"{'='*80}\n")
        
        results = []
        
        for i, alpha in enumerate(alpha_values):
            print(f"\n[{i+1}/{len(alpha_values)}] Running α = {alpha:.2f}...")
            
            # Create config with this alpha value
            network = get_instance_by_name(self.instance_name)
            config = Config(
                network=network,
                optimization=OptimizationConfig(
                    expected_cost_weight=1.0 - lambda_val,
                    cvar_weight=lambda_val,
                    cvar_alpha=alpha
                )
            )
            
            # Generate scenarios
            gen = ScenarioGenerator(config)
            scenarios = gen.generate_scenarios()
            
            # Build and solve model
            model = TwoStageStochasticModel(config, scenarios)
            model.build_model()
            result = model.solve()
            
            if result.status == 'Optimal':
                # Extract key metrics
                total_inventory = sum(result.prepositioned_inventory.values())
                total_emergency = sum(sum(emerg.values()) for emerg in result.scenario_emergency_procurement.values())
                total_unmet = sum(sum(unmet.values()) for unmet in result.scenario_unmet_demand.values())
                
                # Calculate tail size
                tail_size = len([c for c in result.scenario_costs.values() if c >= result.var_value])
                
                results.append({
                    'alpha': alpha,
                    'lambda': lambda_val,
                    'objective': result.objective_value,
                    'expected_cost': result.expected_cost,
                    'var': result.var_value,
                    'cvar': result.cvar_value,
                    'cvar_var_gap': result.cvar_value - result.var_value,
                    'tail_size': tail_size,
                    'tail_pct': (tail_size / len(result.scenario_costs)) * 100,
                    'total_inventory': total_inventory,
                    'total_emergency': total_emergency,
                    'total_unmet': total_unmet,
                    'min_satisfaction_pct': result.min_satisfaction_ratio * 100,
                    'solve_time': result.solve_time,
                    'status': result.status
                })
                
                print(f"   ✓ Objective: ${result.objective_value:,.2f}")
                print(f"   ✓ VaR: ${result.var_value:,.2f}, CVaR: ${result.cvar_value:,.2f}")
                print(f"   ✓ Tail: {tail_size} scenarios ({tail_size/len(result.scenario_costs)*100:.1f}%)")
            else:
                print(f"   ✗ Failed with status: {result.status}")
                results.append({
                    'alpha': alpha,
                    'lambda': lambda_val,
                    'status': result.status,
                    'objective': None,
                })
        
        df = pd.DataFrame(results)
        
        # Save results
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_file = Path(output_dir) / f'cvar_alpha_sweep_{self.instance_name}_lambda{lambda_val:.2f}.csv'
        df.to_csv(output_file, index=False)
        print(f"\n✓ Results saved to {output_file}")
        
        # Generate plots
        self._plot_alpha_results(df, alpha_values, lambda_val, output_dir)
        
        return df
    
    def _plot_risk_weight_results(self, df: pd.DataFrame, lambda_values: List[float], 
                                   alpha: float, output_dir: str):
        """Generate plots for risk weight sweep results."""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle(f'Risk Weight (λ) Sweep - Instance: {self.instance_name}, α={alpha:.2f}', 
                     fontsize=16, fontweight='bold')
        
        # 1. Objective and cost components
        ax = axes[0, 0]
        ax.plot(df['lambda'], df['objective'], 'o-', label='Total Objective', linewidth=2, markersize=8)
        ax.plot(df['lambda'], df['expected_cost'], 's-', label='Expected Cost', linewidth=2, markersize=8)
        ax.plot(df['lambda'], df['cvar'], '^-', label='CVaR', linewidth=2, markersize=8)
        ax.set_xlabel('Risk Weight (λ)', fontsize=12)
        ax.set_ylabel('Cost ($1000 CAD)', fontsize=12)
        ax.set_title('Objective Components vs Risk Weight', fontsize=13)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 2. Inventory levels
        ax = axes[0, 1]
        ax.plot(df['lambda'], df['total_inventory'], 'o-', color='green', linewidth=2, markersize=8)
        ax.set_xlabel('Risk Weight (λ)', fontsize=12)
        ax.set_ylabel('Total Inventory (units)', fontsize=12)
        ax.set_title('Prepositioned Inventory vs Risk Weight', fontsize=13)
        ax.grid(True, alpha=0.3)
        
        # 3. Emergency procurement
        ax = axes[0, 2]
        ax.bar(df['lambda'], df['total_emergency'], alpha=0.7, color='orange')
        ax.set_xlabel('Risk Weight (λ)', fontsize=12)
        ax.set_ylabel('Total Emergency (units)', fontsize=12)
        ax.set_title('Emergency Procurement vs Risk Weight', fontsize=13)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 4. Unmet demand
        ax = axes[1, 0]
        ax.plot(df['lambda'], df['total_unmet'], 'o-', color='red', linewidth=2, markersize=8)
        ax.set_xlabel('Risk Weight (λ)', fontsize=12)
        ax.set_ylabel('Total Unmet Demand (units)', fontsize=12)
        ax.set_title('Unmet Demand vs Risk Weight', fontsize=13)
        ax.grid(True, alpha=0.3)
        
        # 5. Risk premium
        ax = axes[1, 1]
        ax.plot(df['lambda'], df['risk_premium_pct'], 'o-', color='purple', linewidth=2, markersize=8)
        ax.set_xlabel('Risk Weight (λ)', fontsize=12)
        ax.set_ylabel('Risk Premium (%)', fontsize=12)
        ax.set_title('Risk Premium (CVaR/E[Q] - 1) vs Risk Weight', fontsize=13)
        ax.grid(True, alpha=0.3)
        
        # 6. Satisfaction rates
        ax = axes[1, 2]
        ax.plot(df['lambda'], df['min_satisfaction_pct'], 'o-', label='Min', linewidth=2, markersize=8)
        ax.plot(df['lambda'], df['avg_satisfaction_pct'], 's-', label='Avg', linewidth=2, markersize=8)
        ax.set_xlabel('Risk Weight (λ)', fontsize=12)
        ax.set_ylabel('Satisfaction (%)', fontsize=12)
        ax.set_title('Demand Satisfaction vs Risk Weight', fontsize=13)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_file = Path(output_dir) / f'risk_weight_sweep_{self.instance_name}_alpha{alpha:.2f}.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Plot saved to {output_file}")
        plt.close()
    
    def _plot_alpha_results(self, df: pd.DataFrame, alpha_values: List[float],
                           lambda_val: float, output_dir: str):
        """Generate plots for CVaR alpha sweep results."""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f'CVaR Alpha (α) Sweep - Instance: {self.instance_name}, λ={lambda_val:.2f}', 
                     fontsize=16, fontweight='bold')
        
        # 1. VaR and CVaR
        ax = axes[0, 0]
        ax.plot(df['alpha'], df['var'], 'o-', label='VaR', linewidth=2, markersize=8)
        ax.plot(df['alpha'], df['cvar'], 's-', label='CVaR', linewidth=2, markersize=8)
        ax.set_xlabel('CVaR Confidence Level (α)', fontsize=12)
        ax.set_ylabel('Risk Measure ($1000 CAD)', fontsize=12)
        ax.set_title('VaR and CVaR vs α', fontsize=13)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 2. CVaR-VaR gap
        ax = axes[0, 1]
        ax.plot(df['alpha'], df['cvar_var_gap'], 'o-', color='purple', linewidth=2, markersize=8)
        ax.set_xlabel('CVaR Confidence Level (α)', fontsize=12)
        ax.set_ylabel('CVaR - VaR ($1000 CAD)', fontsize=12)
        ax.set_title('Tail Risk Gap vs α', fontsize=13)
        ax.grid(True, alpha=0.3)
        
        # 3. Tail size
        ax = axes[1, 0]
        ax.bar(df['alpha'], df['tail_size'], alpha=0.7, color='orange')
        ax.set_xlabel('CVaR Confidence Level (α)', fontsize=12)
        ax.set_ylabel('Number of Scenarios in Tail', fontsize=12)
        ax.set_title('Tail Size vs α', fontsize=13)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 4. Objective value
        ax = axes[1, 1]
        ax.plot(df['alpha'], df['objective'], 'o-', color='green', linewidth=2, markersize=8)
        ax.set_xlabel('CVaR Confidence Level (α)', fontsize=12)
        ax.set_ylabel('Total Objective ($1000 CAD)', fontsize=12)
        ax.set_title('Objective Value vs α', fontsize=13)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        output_file = Path(output_dir) / f'cvar_alpha_sweep_{self.instance_name}_lambda{lambda_val:.2f}.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Plot saved to {output_file}")
        plt.close()


def run_all_sweeps(instance_name: str = 'small', n_scenarios: int = 100):
    """
    Run all parameter sweeps for a given instance.
    
    Args:
        instance_name: Name of network instance
        n_scenarios: Number of scenarios
    """
    sweep = ParameterSweep(instance_name, n_scenarios)
    
    # Risk weight sweep
    print("\n" + "="*80)
    print("RUNNING RISK WEIGHT SWEEP")
    print("="*80)
    df_lambda = sweep.run_risk_weight_sweep()
    
    # CVaR alpha sweep
    print("\n" + "="*80)
    print("RUNNING CVAR ALPHA SWEEP")
    print("="*80)
    df_alpha = sweep.run_cvar_alpha_sweep()
    
    return df_lambda, df_alpha


if __name__ == "__main__":
    # Run sweeps on small instance
    run_all_sweeps('small', n_scenarios=50)  # Use 50 for faster testing
