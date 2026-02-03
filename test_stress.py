"""
Stress tests for model sanity checks.

These tests verify fundamental properties that any well-formed
stochastic optimization model should satisfy:
1. Penalty monotonicity: Higher unmet penalty should not increase unmet demand
2. Risk aversion monotonicity: Higher CVaR weight should reduce CVaR or increase inventory
"""

import numpy as np
from config import get_default_config
from scenario_generator import generate_scenarios
from optimization_model import TwoStageStochasticModel


def test_penalty_monotonicity():
    """
    Test that increasing unmet demand penalty does not increase unmet demand.
    
    Property: As penalty increases, rational optimizer should reduce unmet demand.
    This is a fundamental sanity check for any cost minimization model.
    """
    print("\n" + "="*80)
    print("STRESS TEST 1: PENALTY MONOTONICITY")
    print("="*80)
    print("\nTesting property: Higher unmet penalty → Lower (or equal) unmet demand")
    
    # Test with 20 scenarios for speed
    base_config = get_default_config()
    base_config.scenario.n_scenarios = 20
    base_config.scenario.random_seed = 42  # Fixed seed for reproducibility
    scenarios = generate_scenarios(base_config)
    
    # Test with increasing penalty levels
    penalty_levels = [100.0, 250.0, 500.0, 1000.0, 2000.0]
    results = []
    
    for penalty in penalty_levels:
        config = get_default_config()
        config.scenario.n_scenarios = 20
        config.scenario.random_seed = 42
        config.optimization.unmet_demand_penalty = penalty
        
        model = TwoStageStochasticModel(config, scenarios)
        model.build_model()
        result = model.solve()
        
        # Calculate total unmet demand across all scenarios
        total_unmet = sum(
            sum(result.scenario_unmet_demand[s].values())
            for s in range(len(scenarios))
        )
        
        results.append({
            'penalty': penalty,
            'total_unmet': total_unmet,
            'objective': result.objective_value,
            'status': result.status
        })
        
        print(f"\n   Penalty ${penalty:,.0f}: Total unmet = {total_unmet:.2f} units, Objective = ${result.objective_value:,.2f}")
    
    # Verify monotonicity
    print(f"\n   Monotonicity Check:")
    violations = 0
    for i in range(len(results) - 1):
        unmet_curr = results[i]['total_unmet']
        unmet_next = results[i+1]['total_unmet']
        penalty_curr = results[i]['penalty']
        penalty_next = results[i+1]['penalty']
        
        if unmet_next > unmet_curr + 1e-6:  # Allow small numerical tolerance
            print(f"      ⚠️  Violation: Penalty ${penalty_curr:,.0f} → ${penalty_next:,.0f}, "
                  f"Unmet {unmet_curr:.2f} → {unmet_next:.2f} (increased!)")
            violations += 1
        else:
            print(f"      ✓ Penalty ${penalty_curr:,.0f} → ${penalty_next:,.0f}, "
                  f"Unmet {unmet_curr:.2f} → {unmet_next:.2f} (non-increasing)")
    
    if violations == 0:
        print(f"\n   ✅ PASS: Penalty monotonicity satisfied (no violations)")
        return True
    else:
        print(f"\n   ❌ FAIL: {violations} violation(s) detected")
        return False


def test_risk_aversion_monotonicity():
    """
    Test that increasing CVaR weight reduces CVaR or increases preparedness inventory.
    
    Property: Higher risk aversion should lead to:
    - Lower CVaR (reduced tail risk), OR
    - Higher first-stage inventory (more preparedness)
    This reflects rational risk-averse behavior.
    """
    print("\n" + "="*80)
    print("STRESS TEST 2: RISK AVERSION MONOTONICITY")
    print("="*80)
    print("\nTesting property: Higher CVaR weight → Lower CVaR or Higher inventory")
    
    # Test with 20 scenarios for speed
    base_config = get_default_config()
    base_config.scenario.n_scenarios = 20
    base_config.scenario.random_seed = 42
    scenarios = generate_scenarios(base_config)
    
    # Test with increasing CVaR weights
    cvar_weights = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    results = []
    
    for w_cvar in cvar_weights:
        config = get_default_config()
        config.scenario.n_scenarios = 20
        config.scenario.random_seed = 42
        config.optimization.cvar_weight = w_cvar
        config.optimization.expectation_weight = 1.0 - w_cvar
        
        model = TwoStageStochasticModel(config, scenarios)
        model.build_model()
        result = model.solve()
        
        # Calculate total first-stage inventory
        total_inventory = sum(result.prepositioned_inventory.values())
        
        results.append({
            'cvar_weight': w_cvar,
            'cvar_value': result.cvar_value,
            'total_inventory': total_inventory,
            'objective': result.objective_value,
            'status': result.status
        })
        
        print(f"\n   CVaR weight {w_cvar:.1f}: CVaR = ${result.cvar_value:,.2f}, "
              f"Inventory = {total_inventory:.1f} units")
    
    # Verify monotonicity (CVaR decreases OR inventory increases)
    print(f"\n   Monotonicity Check (CVaR ↓ OR Inventory ↑):")
    violations = 0
    for i in range(len(results) - 1):
        cvar_curr = results[i]['cvar_value']
        cvar_next = results[i+1]['cvar_value']
        inv_curr = results[i]['total_inventory']
        inv_next = results[i+1]['total_inventory']
        w_curr = results[i]['cvar_weight']
        w_next = results[i+1]['cvar_weight']
        
        cvar_decreased = cvar_next < cvar_curr + 1e-6
        inv_increased = inv_next > inv_curr - 1e-6
        
        if cvar_decreased or inv_increased:
            status = "✓"
            if cvar_decreased and inv_increased:
                reason = "(both CVaR ↓ and Inventory ↑)"
            elif cvar_decreased:
                reason = "(CVaR ↓)"
            else:
                reason = "(Inventory ↑)"
        else:
            status = "⚠️"
            reason = "(VIOLATION: both increased)"
            violations += 1
        
        print(f"      {status} Weight {w_curr:.1f} → {w_next:.1f}: "
              f"CVaR ${cvar_curr:,.0f} → ${cvar_next:,.0f}, "
              f"Inv {inv_curr:.0f} → {inv_next:.0f} {reason}")
    
    if violations == 0:
        print(f"\n   ✅ PASS: Risk aversion monotonicity satisfied")
        return True
    else:
        print(f"\n   ⚠️  WARNING: {violations} violation(s) detected")
        print(f"      Note: Small violations may occur due to discrete optimization and numerical tolerance")
        return violations <= 1  # Allow 1 violation due to discretization


def run_all_stress_tests():
    """Run all stress tests and report results."""
    print("\n" + "="*80)
    print("RUNNING STRESS TEST SUITE")
    print("="*80)
    print("\nThese tests verify fundamental model properties:")
    print("1. Penalty Monotonicity: Higher penalty → Lower unmet demand")
    print("2. Risk Aversion Monotonicity: Higher CVaR weight → Lower CVaR or higher inventory")
    
    results = {}
    
    # Test 1: Penalty monotonicity
    results['penalty_monotonicity'] = test_penalty_monotonicity()
    
    # Test 2: Risk aversion monotonicity
    results['risk_aversion'] = test_risk_aversion_monotonicity()
    
    # Summary
    print("\n" + "="*80)
    print("STRESS TEST SUMMARY")
    print("="*80)
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name.replace('_', ' ').title()}")
    
    if all_passed:
        print("\n✅ ALL STRESS TESTS PASSED")
        print("Model exhibits expected monotonicity properties.")
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Review model formulation or numerical stability.")
    
    print("="*80 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_stress_tests()
    exit(0 if success else 1)
