"""
Example script demonstrating advanced usage of the optimization model.

This script shows how to:
1. Customize network configuration
2. Run sensitivity analysis on parameters
3. Compare different risk strategies
"""

import numpy as np
import matplotlib.pyplot as plt
from config import Config, NetworkConfig, ScenarioConfig, OptimizationConfig
from scenario_generator import generate_scenarios
from optimization_model import TwoStageStochasticModel


def sensitivity_analysis_cvar_weight():
    """
    Perform sensitivity analysis on CVaR weight parameter.
    
    This shows the trade-off between expected cost and risk aversion.
    """
    print("="*80)
    print("SENSITIVITY ANALYSIS: CVaR Weight")
    print("="*80 + "\n")
    
    # Test different CVaR weights
    cvar_weights = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    results = []
    
    for weight in cvar_weights:
        print(f"Testing CVaR weight = {weight:.1f}...")
        
        # Create configuration
        config = Config()
        # PERFORMANCE FIX: Use at least 50 scenarios for reliable CVaR with α=0.90
        # With α=0.90, tail = 10% of scenarios. Need 50+ for stable tail representation.
        config.scenario.n_scenarios = 50
        config.optimization.cvar_weight = weight
        config.optimization.expectation_weight = 1.0 - weight
        
        # Generate scenarios (use same seed for fair comparison)
        config.scenario.random_seed = 42
        scenarios = generate_scenarios(config)
        
        # Solve
        model = TwoStageStochasticModel(config, scenarios)
        model.build_model()
        result = model.solve()
        
        results.append({
            'cvar_weight': weight,
            'objective': result.objective_value,
            'expected_cost': result.expected_cost,
            'cvar': result.cvar_value,
            'inventory': sum(result.prepositioned_inventory.values())
        })
        
        print(f"  Objective: ${result.objective_value:,.2f}")
        print(f"  Expected Cost: ${result.expected_cost:,.2f}")
        print(f"  CVaR: ${result.cvar_value:,.2f}\n")
    
    # Plot results
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    weights = [r['cvar_weight'] for r in results]
    expected = [r['expected_cost'] for r in results]
    cvar = [r['cvar'] for r in results]
    inventory = [r['inventory'] for r in results]
    
    # Plot 1: Cost metrics
    ax1.plot(weights, expected, marker='o', linewidth=2, label='Expected Cost')
    ax1.plot(weights, cvar, marker='s', linewidth=2, label='CVaR')
    ax1.set_xlabel('CVaR Weight', fontsize=12)
    ax1.set_ylabel('Cost ($)', fontsize=12)
    ax1.set_title('Cost Metrics vs CVaR Weight', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Inventory
    ax2.plot(weights, inventory, marker='D', linewidth=2, color='steelblue')
    ax2.set_xlabel('CVaR Weight', fontsize=12)
    ax2.set_ylabel('Total Prepositioned Inventory', fontsize=12)
    ax2.set_title('Inventory vs CVaR Weight', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('sensitivity_cvar_weight.png', dpi=300, bbox_inches='tight')
    print("📊 Saved sensitivity analysis plot to 'sensitivity_cvar_weight.png'\n")
    plt.close()


def sensitivity_analysis_equity():
    """
    Perform sensitivity analysis on minimum demand satisfaction parameter.
    
    This shows the cost of enforcing equity constraints.
    """
    print("="*80)
    print("SENSITIVITY ANALYSIS: Minimum Demand Satisfaction")
    print("="*80 + "\n")
    
    # Test different equity requirements
    min_satisfactions = [0.60, 0.70, 0.75, 0.80, 0.85, 0.90]
    results = []
    
    for min_sat in min_satisfactions:
        print(f"Testing minimum satisfaction = {min_sat:.0%}...")
        
        # Create configuration
        config = Config()
        # PERFORMANCE FIX: Use at least 50 scenarios for reliable CVaR with α=0.90
        config.scenario.n_scenarios = 50
        config.optimization.min_demand_satisfaction = min_sat
        
        # Generate scenarios (use same seed for fair comparison)
        config.scenario.random_seed = 42
        scenarios = generate_scenarios(config)
        
        # Solve
        model = TwoStageStochasticModel(config, scenarios)
        model.build_model()
        result = model.solve()
        
        results.append({
            'min_satisfaction': min_sat,
            'objective': result.objective_value,
            'actual_min_sat': result.min_satisfaction_ratio,
            'actual_avg_sat': result.avg_satisfaction_ratio,
        })
        
        print(f"  Objective: ${result.objective_value:,.2f}")
        print(f"  Actual Min Satisfaction: {result.min_satisfaction_ratio:.1%}")
        print(f"  Actual Avg Satisfaction: {result.avg_satisfaction_ratio:.1%}\n")
    
    # Plot results
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    min_sats = [r['min_satisfaction'] * 100 for r in results]
    objectives = [r['objective'] for r in results]
    actual_mins = [r['actual_min_sat'] * 100 for r in results]
    actual_avgs = [r['actual_avg_sat'] * 100 for r in results]
    
    # Plot 1: Cost vs equity requirement
    ax1.plot(min_sats, objectives, marker='o', linewidth=2, color='coral')
    ax1.set_xlabel('Minimum Demand Satisfaction Required (%)', fontsize=12)
    ax1.set_ylabel('Total Cost ($)', fontsize=12)
    ax1.set_title('Cost of Equity Constraints', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Required vs actual satisfaction
    ax2.plot(min_sats, min_sats, linestyle='--', color='gray', label='Required')
    ax2.plot(min_sats, actual_mins, marker='s', linewidth=2, label='Actual Min')
    ax2.plot(min_sats, actual_avgs, marker='D', linewidth=2, label='Actual Avg')
    ax2.set_xlabel('Minimum Demand Satisfaction Required (%)', fontsize=12)
    ax2.set_ylabel('Demand Satisfaction (%)', fontsize=12)
    ax2.set_title('Required vs Actual Satisfaction', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('sensitivity_equity.png', dpi=300, bbox_inches='tight')
    print("📊 Saved sensitivity analysis plot to 'sensitivity_equity.png'\n")
    plt.close()


def compare_risk_strategies():
    """
    Compare different risk management strategies.
    
    Compares:
    1. Risk-neutral (only expected cost)
    2. Balanced (50% expected, 50% CVaR)
    3. Risk-averse (only CVaR)
    """
    print("="*80)
    print("COMPARISON: Risk Management Strategies")
    print("="*80 + "\n")
    
    strategies = [
        ('Risk-Neutral', 0.0),
        ('Balanced', 0.5),
        ('Risk-Averse', 1.0),
    ]
    
    results = []
    
    for name, cvar_weight in strategies:
        print(f"Strategy: {name} (CVaR weight = {cvar_weight:.1f})")
        
        # Create configuration
        config = Config()
        # PERFORMANCE FIX: Use at least 50 scenarios for reliable CVaR with α=0.90
        config.scenario.n_scenarios = 50
        config.optimization.cvar_weight = cvar_weight
        config.optimization.expectation_weight = 1.0 - cvar_weight
        
        # Generate scenarios
        config.scenario.random_seed = 42
        scenarios = generate_scenarios(config)
        
        # Solve
        model = TwoStageStochasticModel(config, scenarios)
        model.build_model()
        result = model.solve()
        
        # Extract scenario costs
        scenario_costs = [result.scenario_costs[s] for s in sorted(result.scenario_costs.keys())]
        
        results.append({
            'name': name,
            'objective': result.objective_value,
            'expected_cost': result.expected_cost,
            'cvar': result.cvar_value,
            'var': result.var_value,
            'scenario_costs': scenario_costs,
            'inventory': result.prepositioned_inventory,
        })
        
        print(f"  Objective: ${result.objective_value:,.2f}")
        print(f"  Expected Cost: ${result.expected_cost:,.2f}")
        print(f"  VaR (95%): ${result.var_value:,.2f}")
        print(f"  CVaR (95%): ${result.cvar_value:,.2f}")
        print(f"  Total Inventory: {sum(result.prepositioned_inventory.values()):,.1f} units\n")
    
    # Create comparison plot
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: Cost metrics comparison
    names = [r['name'] for r in results]
    expected = [r['expected_cost'] for r in results]
    var_vals = [r['var'] for r in results]
    cvar_vals = [r['cvar'] for r in results]
    
    x = np.arange(len(names))
    width = 0.25
    
    ax1.bar(x - width, expected, width, label='Expected', color='steelblue')
    ax1.bar(x, var_vals, width, label='VaR (95%)', color='orange')
    ax1.bar(x + width, cvar_vals, width, label='CVaR (95%)', color='coral')
    ax1.set_ylabel('Cost ($)', fontsize=12)
    ax1.set_title('Risk Metrics by Strategy', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(names)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Cost distributions
    for r in results:
        ax2.hist(r['scenario_costs'], bins=15, alpha=0.5, label=r['name'])
    ax2.set_xlabel('Cost ($)', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    ax2.set_title('Cost Distribution by Strategy', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Inventory allocation
    dcs = sorted(results[0]['inventory'].keys())
    x = np.arange(len(dcs))
    width = 0.25
    
    for i, r in enumerate(results):
        inventories = [r['inventory'][dc] for dc in dcs]
        ax3.bar(x + i*width - width, inventories, width, label=r['name'])
    
    ax3.set_ylabel('Inventory (units)', fontsize=12)
    ax3.set_title('Inventory Allocation by Strategy', fontsize=14, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(dcs)
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Cumulative cost distribution
    for r in results:
        sorted_costs = np.sort(r['scenario_costs'])
        cumulative = np.arange(1, len(sorted_costs) + 1) / len(sorted_costs)
        ax4.plot(sorted_costs, cumulative * 100, linewidth=2, label=r['name'], marker='o')
    
    ax4.axhline(y=95, color='gray', linestyle='--', alpha=0.5)
    ax4.set_xlabel('Cost ($)', fontsize=12)
    ax4.set_ylabel('Cumulative Probability (%)', fontsize=12)
    ax4.set_title('Cumulative Distribution by Strategy', fontsize=14, fontweight='bold')
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('strategy_comparison.png', dpi=300, bbox_inches='tight')
    print("📊 Saved strategy comparison plot to 'strategy_comparison.png'\n")
    plt.close()


def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("ADVANCED USAGE EXAMPLES")
    print("="*80 + "\n")
    
    # Run sensitivity analyses
    sensitivity_analysis_cvar_weight()
    sensitivity_analysis_equity()
    
    # Compare strategies
    compare_risk_strategies()
    
    print("="*80)
    print("✅ ALL EXAMPLES COMPLETED")
    print("="*80 + "\n")
    print("Generated files:")
    print("  - sensitivity_cvar_weight.png")
    print("  - sensitivity_equity.png")
    print("  - strategy_comparison.png")


if __name__ == "__main__":
    main()
