"""
Baseline models for comparison against the full two-stage stochastic MILP.

This module implements various baseline strategies to demonstrate the value
of different model components (CVaR, prepositioning, equity constraints).
"""

import numpy as np
from typing import Dict, List
from dataclasses import dataclass
from config import Config
from scenario_generator import ScenarioGenerator
from optimization_model import TwoStageStochasticModel


@dataclass
class BaselineResult:
    """Results from a baseline model run."""
    name: str
    objective: float
    expected_cost: float
    var_90: float
    cvar_90: float
    total_unmet: float
    min_satisfaction: float
    avg_satisfaction: float
    total_inventory: float
    solve_time: float
    status: str


class BaselineModels:
    """Collection of baseline models for comparison."""
    
    def __init__(self, config: Config):
        self.config = config
        self.scenario_gen = ScenarioGenerator(config)
    
    def run_all_baselines(self, scenarios: List[Dict]) -> List[BaselineResult]:
        """
        Run all baseline models and return results.
        
        Args:
            scenarios: List of scenario objects
            
        Returns:
            List of BaselineResult objects
        """
        results = []
        
        # 1. Full model (for comparison)
        print("\n1/5 Running full model (reference)...")
        results.append(self._run_full_model(scenarios))
        
        # 2. Expected cost only (no CVaR, no risk aversion)
        print("2/5 Running expected-cost-only baseline...")
        results.append(self._run_expected_cost_only(scenarios))
        
        # 3. No equity constraints
        print("3/5 Running no-equity baseline...")
        results.append(self._run_no_equity(scenarios))
        
        # 4. Risk-neutral (CVaR weight = 0)
        print("4/5 Running risk-neutral baseline...")
        results.append(self._run_risk_neutral(scenarios))
        
        # 5. Risk-only (CVaR weight = 1.0)
        print("5/5 Running risk-only baseline...")
        results.append(self._run_risk_only(scenarios))
        
        return results
    
    def _extract_result(self, name: str, result) -> BaselineResult:
        """Extract baseline result from optimization result."""
        total_unmet = sum(sum(result.scenario_unmet_demand[s].values()) 
                         for s in result.scenario_unmet_demand.keys())
        
        total_inv = sum(result.prepositioned_inventory.values())
        
        return BaselineResult(
            name=name,
            objective=result.objective_value,
            expected_cost=result.expected_cost,
            var_90=result.var_value,
            cvar_90=result.cvar_value,
            total_unmet=total_unmet,
            min_satisfaction=result.min_satisfaction_ratio,
            avg_satisfaction=result.avg_satisfaction_ratio,
            total_inventory=total_inv,
            solve_time=result.solve_time,
            status=result.status
        )
    
    def _run_full_model(self, scenarios: List[Dict]) -> BaselineResult:
        """Run full model with all features."""
        model = TwoStageStochasticModel(self.config, scenarios)
        model.build_model()
        result = model.solve()
        return self._extract_result("Full Model", result)
    
    def _run_expected_cost_only(self, scenarios: List[Dict]) -> BaselineResult:
        """Run model with CVaR weight = 0."""
        original_weight = self.config.optimization.cvar_weight
        self.config.optimization.cvar_weight = 0.0
        
        model = TwoStageStochasticModel(self.config, scenarios)
        model.build_model()
        result = model.solve()
        
        self.config.optimization.cvar_weight = original_weight
        return self._extract_result("Expected Cost Only (λ=0)", result)
    
    def _run_no_equity(self, scenarios: List[Dict]) -> BaselineResult:
        """Run model without equity constraints."""
        original_min_sat = self.config.optimization.min_satisfaction
        self.config.optimization.min_satisfaction = 0.0
        
        model = TwoStageStochasticModel(self.config, scenarios)
        model.build_model()
        result = model.solve()
        
        self.config.optimization.min_satisfaction = original_min_sat
        return self._extract_result("No Equity Constraints", result)
    
    def _run_risk_neutral(self, scenarios: List[Dict]) -> BaselineResult:
        """Run with CVaR weight = 0."""
        original_weight = self.config.optimization.cvar_weight
        self.config.optimization.cvar_weight = 0.0
        
        model = TwoStageStochasticModel(self.config, scenarios)
        model.build_model()
        result = model.solve()
        
        self.config.optimization.cvar_weight = original_weight
        return self._extract_result("Risk Neutral (λ=0)", result)
    
    def _run_risk_only(self, scenarios: List[Dict]) -> BaselineResult:
        """Run with CVaR weight = 1.0."""
        original_weight = self.config.optimization.cvar_weight
        self.config.optimization.cvar_weight = 1.0
        
        model = TwoStageStochasticModel(self.config, scenarios)
        model.build_model()
        result = model.solve()
        
        self.config.optimization.cvar_weight = original_weight
        return self._extract_result("Risk Only (λ=1)", result)
    
    @staticmethod
    def print_comparison_table(results: List[BaselineResult]):
        """Print a comparison table of all baseline results."""
        print("\n" + "=" * 135)
        print("BASELINE COMPARISON TABLE")
        print("=" * 135)
        
        # Header
        print(f"{'Model':<30} {'Obj ($K)':<12} {'E[Cost]':<12} {'CVaR':<12} {'Premium':<12} "
              f"{'Unmet':<10} {'Min Sat':<10} {'Inventory':<10} {'Time (s)':<10}")
        print("-" * 135)
        
        # Rows
        for r in results:
            premium = ((r.cvar_90 / r.expected_cost - 1) * 100) if r.expected_cost > 0 else 0
            print(f"{r.name:<30} {r.objective:<12.2f} {r.expected_cost:<12.2f} {r.cvar_90:<12.2f} "
                  f"{premium:>10.1f}% {r.total_unmet:<10.1f} {r.min_satisfaction:<10.1%} "
                  f"{r.total_inventory:<10.1f} {r.solve_time:<10.3f}")
        
        print("=" * 135)
        
        # Analysis
        full_model = [r for r in results if "Full Model" in r.name][0]
        
        print("\n" + "=" * 135)
        print("KEY FINDINGS (vs Full Model):")
        print("=" * 135)
        
        for r in results:
            if "Full Model" in r.name:
                continue
            
            cost_diff = ((r.expected_cost / full_model.expected_cost - 1) * 100)
            cvar_diff = ((r.cvar_90 / full_model.cvar_90 - 1) * 100)
            unmet_diff = r.total_unmet - full_model.total_unmet
            inv_diff = r.total_inventory - full_model.total_inventory
            
            print(f"\n{r.name}:")
            print(f"  Expected cost: {cost_diff:+.2f}%")
            print(f"  CVaR: {cvar_diff:+.2f}%")
            print(f"  Additional unmet demand: {unmet_diff:+.2f} units")
            print(f"  Inventory change: {inv_diff:+.2f} units")
            print(f"  Min satisfaction: {r.min_satisfaction:.1%} vs {full_model.min_satisfaction:.1%}")
        
        print("\n" + "=" * 135)


def main():
    """Example usage."""
    from config import get_default_config
    
    print("=" * 80)
    print("BASELINE MODEL COMPARISON STUDY")
    print("=" * 80)
    print("\nRunning baseline comparisons...")
    
    config = get_default_config()
    
    # Generate scenarios
    scenario_gen = ScenarioGenerator(config)
    scenarios = scenario_gen.generate_scenarios(n_scenarios=50)  # Use 50 for faster testing
    
    # Run baselines
    baseline_models = BaselineModels(config)
    results = baseline_models.run_all_baselines(scenarios)
    
    # Print comparison
    BaselineModels.print_comparison_table(results)
    
    print("\n✅ Baseline comparison complete!")
    print("\nInterpretation:")
    print("- Expected Cost Only: Shows value of risk consideration")
    print("- No Equity: Shows cost of fairness requirements")
    print("- Risk Neutral: Pure expected cost minimization")
    print("- Risk Only: Maximum risk aversion")


if __name__ == "__main__":
    main()
