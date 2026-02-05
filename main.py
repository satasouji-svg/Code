"""
Main execution script for wildfire-resilient supply network optimization.
Runs baseline experiments and parameter sweeps.
"""

import argparse
from pathlib import Path
from config import get_default_config
from scenario_gen import ScenarioGenerator
from model import WildfireSupplyNetworkModel
from solver import OptimizationSolver
from reporter import ResultReporter
from visualizer import ResultVisualizer
from validation import ModelValidator
from experiments import ExperimentRunner


def run_quick_demo():
    """Run a quick demonstration of the optimization model."""
    print("\n" + "="*70)
    print(" WILDFIRE-RESILIENT SUPPLY NETWORK OPTIMIZATION - QUICK DEMO")
    print("="*70 + "\n")
    
    # Load configuration
    network_config, model_params, scenario_params = get_default_config()
    
    # Generate scenarios
    print("Generating scenarios...")
    scenario_gen = ScenarioGenerator(network_config, scenario_params)
    scenarios = scenario_gen.generate_scenarios(model_params.num_scenarios)
    
    # Display scenario summary
    scenario_summary = scenario_gen.get_scenario_summary(scenarios)
    print(f"\nGenerated {len(scenarios)} scenarios")
    print(f"Total demand range: {scenario_summary['total_demand'].min():.1f} - "
          f"{scenario_summary['total_demand'].max():.1f}")
    print(f"Disruption range: {scenario_summary['num_disruptions'].min():.0f} - "
          f"{scenario_summary['num_disruptions'].max():.0f} arcs")
    
    # Validate scenarios
    print("\nValidating scenarios...")
    validator = ModelValidator()
    prob_validation = validator.validate_scenario_probabilities(scenarios)
    if prob_validation['valid']:
        print("✓ Scenario probabilities validated")
    else:
        print("✗ Scenario validation failed:")
        for error in prob_validation['errors']:
            print(f"  {error}")
    
    # Build model
    print("\nBuilding optimization model...")
    model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
    pyomo_model = model.build_model()
    
    # Validate model structure
    print("\nValidating model structure...")
    structure_validation = validator.validate_model_structure(pyomo_model)
    if structure_validation['valid']:
        print("✓ Model structure validated")
    else:
        print("✗ Model structure validation failed:")
        for error in structure_validation['errors']:
            print(f"  {error}")
        return
    
    # Solve model
    print("\nSolving optimization model...")
    solver = OptimizationSolver()
    solution = solver.solve(pyomo_model, tee=False)
    
    if solution['status'] != 'optimal':
        print(f"✗ Optimization failed: {solution['status']}")
        if 'message' in solution:
            print(f"  {solution['message']}")
        return
    
    print(f"✓ Optimization completed in {solution['solve_time']:.2f} seconds")
    
    # Validate solution
    print("\nValidating solution feasibility...")
    feasibility_validation = validator.validate_solution_feasibility(pyomo_model)
    validator.print_validation_report(feasibility_validation)
    
    # Generate reports
    print("\nGenerating reports and visualizations...")
    reporter = ResultReporter()
    visualizer = ResultVisualizer()
    
    reporter.print_summary(solution)
    reporter.generate_summary_report(solution, "quick_demo")
    reporter.generate_cost_breakdown(solution, "quick_demo")
    reporter.generate_service_level_table(solution, "quick_demo")
    reporter.generate_scenario_cost_table(solution, "quick_demo")
    reporter.generate_first_stage_decisions_table(solution, "quick_demo")
    reporter.save_solution_json(solution, "quick_demo")
    
    # Generate visualizations
    visualizer.plot_scenario_cost_distribution(solution, "quick_demo")
    visualizer.plot_first_stage_decisions(solution, "quick_demo")
    
    zones = network_config.demand_zones
    visualizer.plot_service_level_heatmap(solution, zones, "quick_demo")
    visualizer.plot_fairness_analysis(solution, "quick_demo")
    
    print("\n" + "="*70)
    print(" DEMO COMPLETED SUCCESSFULLY")
    print("="*70)
    print("\nResults saved to 'results/' directory")
    print("Figures saved to 'results/figures/' directory")


def run_baseline_experiments():
    """Run comprehensive baseline experiments."""
    print("\n" + "="*70)
    print(" RUNNING BASELINE EXPERIMENTS")
    print("="*70 + "\n")
    
    network_config, model_params, scenario_params = get_default_config()
    
    runner = ExperimentRunner(network_config, model_params, scenario_params)
    results = runner.run_baseline_experiments()
    
    print("\n✓ Baseline experiments completed")
    print("  Results saved to 'results/' directory")


def run_parameter_sweeps():
    """Run parameter sweep experiments."""
    print("\n" + "="*70)
    print(" RUNNING PARAMETER SWEEPS")
    print("="*70 + "\n")
    
    network_config, model_params, scenario_params = get_default_config()
    
    runner = ExperimentRunner(network_config, model_params, scenario_params)
    
    # Lambda sweep (risk aversion)
    print("\n--- Lambda (Risk Aversion) Sweep ---")
    lambda_values = [0.0, 0.25, 0.5, 0.75, 1.0]
    runner.run_parameter_sweep_lambda(lambda_values)
    
    # Alpha sweep (CVaR confidence)
    print("\n--- Alpha (CVaR Confidence) Sweep ---")
    alpha_values = [0.90, 0.95, 0.99]
    runner.run_parameter_sweep_alpha(alpha_values)
    
    # Beta sweep (minimum service level)
    print("\n--- Beta (Minimum Service) Sweep ---")
    beta_values = [0.6, 0.7, 0.8, 0.9]
    runner.run_parameter_sweep_beta(beta_values)
    
    # Budget sweep
    print("\n--- Hardening Budget Sweep ---")
    budget_values = [0, 5000, 10000, 15000, 20000]
    runner.run_parameter_sweep_budget(budget_values)
    
    print("\n✓ Parameter sweeps completed")
    print("  Results saved to 'results/' directory")


def main():
    """Main entry point with command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Wildfire-Resilient Supply Network Optimization'
    )
    parser.add_argument(
        '--mode',
        choices=['demo', 'baseline', 'sweeps', 'all'],
        default='demo',
        help='Execution mode: demo (quick), baseline (experiments), sweeps (parameter sweeps), or all'
    )
    
    args = parser.parse_args()
    
    # Create output directories
    Path("results").mkdir(exist_ok=True)
    Path("results/figures").mkdir(exist_ok=True)
    
    if args.mode == 'demo':
        run_quick_demo()
    elif args.mode == 'baseline':
        run_baseline_experiments()
    elif args.mode == 'sweeps':
        run_parameter_sweeps()
    elif args.mode == 'all':
        run_quick_demo()
        run_baseline_experiments()
        run_parameter_sweeps()
    
    print("\n" + "="*70)
    print(" ALL OPERATIONS COMPLETED")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
