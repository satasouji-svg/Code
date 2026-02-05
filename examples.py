"""
Example: Custom Configuration
Demonstrates how to customize the network and parameters for different scenarios.
"""

from config import NetworkConfig, ModelParameters, ScenarioParameters
from scenario_gen import ScenarioGenerator
from model import WildfireSupplyNetworkModel
from solver import OptimizationSolver
from reporter import ResultReporter
from visualizer import ResultVisualizer


def example_1_high_risk_aversion():
    """Example 1: High risk aversion scenario."""
    print("\n=== Example 1: High Risk Aversion ===")
    
    # Create custom configuration
    network = NetworkConfig()
    params = ModelParameters()
    scenario_params = ScenarioParameters()
    
    # Set high risk aversion
    params.lambda_risk = 0.9  # Very risk-averse
    params.alpha_cvar = 0.99  # 99% confidence level
    params.hardening_budget = 20000  # Higher budget for resilience
    
    # Generate scenarios
    gen = ScenarioGenerator(network, scenario_params)
    scenarios = gen.generate_scenarios(15)
    
    # Build and solve model
    model = WildfireSupplyNetworkModel(network, params, scenarios)
    pyomo_model = model.build_model()
    
    solver = OptimizationSolver()
    solution = solver.solve(pyomo_model)
    
    # Generate reports
    reporter = ResultReporter(output_dir="results/examples")
    if solution['status'] == 'optimal':
        reporter.print_summary(solution)
        reporter.generate_summary_report(solution, "high_risk_aversion")
    
    return solution


def example_2_equity_focused():
    """Example 2: Equity-focused with strict minimum service."""
    print("\n=== Example 2: Equity-Focused ===")
    
    network = NetworkConfig()
    params = ModelParameters()
    scenario_params = ScenarioParameters()
    
    # Set equity parameters
    params.equity_mode = 1  # Minimum service level mode
    params.beta_min_service = 0.95  # 95% minimum service
    params.lambda_risk = 0.3  # Moderate risk aversion
    
    # Generate scenarios
    gen = ScenarioGenerator(network, scenario_params)
    scenarios = gen.generate_scenarios(15)
    
    # Build and solve model
    model = WildfireSupplyNetworkModel(network, params, scenarios)
    pyomo_model = model.build_model()
    
    solver = OptimizationSolver()
    solution = solver.solve(pyomo_model)
    
    # Generate reports
    reporter = ResultReporter(output_dir="results/examples")
    visualizer = ResultVisualizer(output_dir="results/examples/figures")
    
    if solution['status'] == 'optimal':
        reporter.print_summary(solution)
        reporter.generate_summary_report(solution, "equity_focused")
        visualizer.plot_fairness_analysis(solution, "equity_focused")
    
    return solution


def example_3_large_network():
    """Example 3: Larger network with more nodes."""
    print("\n=== Example 3: Large Network ===")
    
    # Create custom network
    network = NetworkConfig()
    
    # Add more demand zones
    network.demand_zones = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5', 'Z6']
    for zone in ['Z5', 'Z6']:
        network.base_demand[zone] = 45
    
    # Add more arcs
    new_arcs = [('DC1', 'Z5'), ('DC2', 'Z6'), ('DC3', 'Z5')]
    network.dc_zone_arcs.extend(new_arcs)
    
    # Update costs for new arcs
    for arc in new_arcs:
        network.transport_cost[arc] = 8.0
        network.hardening_cost[arc] = 3000.0  # Add hardening costs
    
    params = ModelParameters()
    scenario_params = ScenarioParameters()
    
    # Generate scenarios
    gen = ScenarioGenerator(network, scenario_params)
    scenarios = gen.generate_scenarios(20)
    
    # Build and solve model
    model = WildfireSupplyNetworkModel(network, params, scenarios)
    pyomo_model = model.build_model()
    
    solver = OptimizationSolver()
    solution = solver.solve(pyomo_model)
    
    # Generate reports
    reporter = ResultReporter(output_dir="results/examples")
    if solution['status'] == 'optimal':
        reporter.print_summary(solution)
        reporter.generate_summary_report(solution, "large_network")
    
    return solution


def example_4_high_disruption():
    """Example 4: High disruption probability scenario."""
    print("\n=== Example 4: High Disruption Probability ===")
    
    network = NetworkConfig()
    params = ModelParameters()
    scenario_params = ScenarioParameters()
    
    # Set high disruption probability
    scenario_params.disruption_prob_base = 0.35  # 35% base probability
    scenario_params.spatial_correlation = True
    
    # Increase hardening budget to compensate
    params.hardening_budget = 25000
    params.lambda_risk = 0.7  # Higher risk aversion
    
    # Generate scenarios
    gen = ScenarioGenerator(network, scenario_params)
    scenarios = gen.generate_scenarios(25)
    
    # Build and solve model
    model = WildfireSupplyNetworkModel(network, params, scenarios)
    pyomo_model = model.build_model()
    
    solver = OptimizationSolver()
    solution = solver.solve(pyomo_model)
    
    # Generate reports
    reporter = ResultReporter(output_dir="results/examples")
    visualizer = ResultVisualizer(output_dir="results/examples/figures")
    
    if solution['status'] == 'optimal':
        reporter.print_summary(solution)
        reporter.generate_summary_report(solution, "high_disruption")
        visualizer.plot_scenario_cost_distribution(solution, "high_disruption")
    
    return solution


def example_5_cost_minimization():
    """Example 5: Pure cost minimization (risk-neutral)."""
    print("\n=== Example 5: Cost Minimization ===")
    
    network = NetworkConfig()
    params = ModelParameters()
    scenario_params = ScenarioParameters()
    
    # Risk-neutral approach
    params.lambda_risk = 0.0  # No risk aversion
    params.hardening_budget = 5000  # Minimal hardening
    
    # Generate scenarios
    gen = ScenarioGenerator(network, scenario_params)
    scenarios = gen.generate_scenarios(15)
    
    # Build and solve model
    model = WildfireSupplyNetworkModel(network, params, scenarios)
    pyomo_model = model.build_model()
    
    solver = OptimizationSolver()
    solution = solver.solve(pyomo_model)
    
    # Generate reports
    reporter = ResultReporter(output_dir="results/examples")
    if solution['status'] == 'optimal':
        reporter.print_summary(solution)
        reporter.generate_summary_report(solution, "cost_minimization")
    
    return solution


if __name__ == "__main__":
    import os
    os.makedirs("results/examples", exist_ok=True)
    os.makedirs("results/examples/figures", exist_ok=True)
    
    print("\n" + "="*70)
    print(" RUNNING CUSTOM CONFIGURATION EXAMPLES")
    print("="*70)
    
    # Run all examples
    example_1_high_risk_aversion()
    example_2_equity_focused()
    example_3_large_network()
    example_4_high_disruption()
    example_5_cost_minimization()
    
    print("\n" + "="*70)
    print(" ALL EXAMPLES COMPLETED")
    print("="*70)
    print("\nResults saved to 'results/examples/' directory")
