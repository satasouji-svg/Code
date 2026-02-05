#!/usr/bin/env python
"""
Query script to display current configuration information.
Run with: python info.py
"""

from config import get_default_config


def print_config_info():
    """Print configuration information."""
    network_config, model_params, scenario_params = get_default_config()
    
    print("="*70)
    print("WILDFIRE-RESILIENT SUPPLY NETWORK - CONFIGURATION INFO")
    print("="*70)
    print()
    
    # Scenarios
    print("📊 SCENARIOS")
    print("-" * 70)
    print(f"  Number of Scenarios: {model_params.num_scenarios}")
    print(f"  Probability per Scenario: {1.0/model_params.num_scenarios:.4f} ({100.0/model_params.num_scenarios:.2f}%)")
    print(f"  Random Seed: {scenario_params.random_seed}")
    print()
    
    # Network Structure
    print("🌐 NETWORK STRUCTURE")
    print("-" * 70)
    print(f"  Suppliers: {len(network_config.suppliers)} ({', '.join(network_config.suppliers)})")
    print(f"  Distribution Centers: {len(network_config.distribution_centers)} ({', '.join(network_config.distribution_centers)})")
    print(f"  Demand Zones: {len(network_config.demand_zones)} ({', '.join(network_config.demand_zones)})")
    print(f"  Supplier-DC Arcs: {len(network_config.supplier_dc_arcs)}")
    print(f"  DC-Zone Arcs: {len(network_config.dc_zone_arcs)}")
    print(f"  Emergency Arcs: {len(network_config.emergency_arcs)}")
    print()
    
    # Risk Parameters
    print("⚠️  RISK PARAMETERS")
    print("-" * 70)
    print(f"  Risk Aversion (λ): {model_params.lambda_risk:.2f}")
    print(f"  CVaR Confidence (α): {model_params.alpha_cvar:.2f} ({model_params.alpha_cvar*100:.0f}%)")
    print(f"  Equity Mode: {model_params.equity_mode}")
    if model_params.equity_mode == 1:
        print(f"  Minimum Service Level (β): {model_params.beta_min_service:.2f} ({model_params.beta_min_service*100:.0f}%)")
    print()
    
    # Budget
    print("💰 BUDGET")
    print("-" * 70)
    print(f"  Hardening Budget: ${model_params.hardening_budget:,.2f}")
    print()
    
    # Uncertainty Parameters
    print("🎲 UNCERTAINTY PARAMETERS")
    print("-" * 70)
    print(f"  Demand Correlation: {scenario_params.demand_correlation:.2f}")
    print(f"  Demand Surge Range: {scenario_params.demand_surge_min:.1f}x to {scenario_params.demand_surge_max:.1f}x")
    print(f"  Arc Disruption Probability: {scenario_params.disruption_prob_base:.2%}")
    print(f"  Spatial Correlation: {'Enabled' if scenario_params.spatial_correlation else 'Disabled'}")
    print()
    
    # Total Demand
    total_base_demand = sum(network_config.base_demand.values())
    print("📦 DEMAND")
    print("-" * 70)
    print(f"  Total Base Demand: {total_base_demand:.1f} tons")
    print(f"  Expected Demand Range: {total_base_demand * scenario_params.demand_surge_min:.1f} to {total_base_demand * scenario_params.demand_surge_max:.1f} tons")
    print()
    
    # Capacities
    total_supplier_capacity = sum(network_config.supplier_capacity.values())
    total_dc_capacity = sum(network_config.dc_storage_capacity.values())
    print("🏭 CAPACITIES")
    print("-" * 70)
    print(f"  Total Supplier Capacity: {total_supplier_capacity:.1f} tons")
    print(f"  Total DC Storage Capacity: {total_dc_capacity:.1f} tons")
    print()
    
    print("="*70)
    print()
    print("💡 TIP: To change these values, modify config.py")
    print("📖 For more info on scenarios, see SCENARIOS_FAQ.md")
    print()


if __name__ == "__main__":
    print_config_info()
