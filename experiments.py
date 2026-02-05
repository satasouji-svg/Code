"""
Experimental design module for baseline experiments and parameter sweeps.
Includes risk-neutral, no-resilience, and no-prepositioning baselines.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from config import NetworkConfig, ModelParameters, ScenarioParameters
from scenario_gen import ScenarioGenerator
from model import WildfireSupplyNetworkModel
from solver import OptimizationSolver
from reporter import ResultReporter
from visualizer import ResultVisualizer


class ExperimentRunner:
    """Run experiments with different configurations."""
    
    def __init__(self, network_config: NetworkConfig,
                 base_model_params: ModelParameters,
                 scenario_params: ScenarioParameters):
        self.network = network_config
        self.base_params = base_model_params
        self.scenario_params = scenario_params
        self.reporter = ResultReporter()
        self.visualizer = ResultVisualizer()
    
    def run_baseline_experiments(self) -> Dict[str, Any]:
        """Run baseline experiments for comparison."""
        results = {}
        
        print("\n" + "="*60)
        print("RUNNING BASELINE EXPERIMENTS")
        print("="*60)
        
        # Generate scenarios once for all baselines
        scenario_gen = ScenarioGenerator(self.network, self.scenario_params)
        scenarios = scenario_gen.generate_scenarios(self.base_params.num_scenarios)
        
        # 1. Full model (with all features)
        print("\n1. Full Model (CVaR + Hardening + Prepositioning)")
        results['full_model'] = self._run_single_experiment(
            scenarios, self.base_params, "full_model"
        )
        
        # 2. Risk-neutral model (lambda = 0)
        print("\n2. Risk-Neutral Model (lambda=0)")
        params_risk_neutral = ModelParameters()
        params_risk_neutral.lambda_risk = 0.0
        results['risk_neutral'] = self._run_single_experiment(
            scenarios, params_risk_neutral, "risk_neutral"
        )
        
        # 3. No-resilience model (hardening budget = 0)
        print("\n3. No-Resilience Model (no hardening)")
        params_no_resilience = ModelParameters()
        params_no_resilience.hardening_budget = 0.0
        results['no_resilience'] = self._run_single_experiment(
            scenarios, params_no_resilience, "no_resilience"
        )
        
        # 4. No-prepositioning model (prepositioning cost = very high)
        print("\n4. No-Prepositioning Model")
        network_no_prepos = NetworkConfig()
        for dc in network_no_prepos.distribution_centers:
            network_no_prepos.prepositioning_cost[dc] = 1000.0  # Very high cost
        params_no_prepos = ModelParameters()
        
        # Need to regenerate scenarios with new network config
        scenario_gen_no_prepos = ScenarioGenerator(network_no_prepos, self.scenario_params)
        scenarios_no_prepos = scenario_gen_no_prepos.generate_scenarios(
            self.base_params.num_scenarios
        )
        
        model = WildfireSupplyNetworkModel(
            network_no_prepos, params_no_prepos, scenarios_no_prepos
        )
        pyomo_model = model.build_model()
        solver = OptimizationSolver()
        solution = solver.solve(pyomo_model)
        results['no_prepositioning'] = solution
        
        if solution['status'] == 'optimal':
            self.reporter.generate_summary_report(solution, "no_prepositioning")
        
        print("\n" + "="*60)
        print("BASELINE EXPERIMENTS COMPLETED")
        print("="*60)
        
        # Generate comparison report
        self._generate_baseline_comparison(results)
        
        return results
    
    def run_parameter_sweep_lambda(self, lambda_values: List[float]) -> pd.DataFrame:
        """Sweep risk aversion parameter (lambda)."""
        print(f"\nRunning lambda sweep: {lambda_values}")
        
        scenario_gen = ScenarioGenerator(self.network, self.scenario_params)
        scenarios = scenario_gen.generate_scenarios(self.base_params.num_scenarios)
        
        results = []
        for lambda_val in lambda_values:
            print(f"\nTesting lambda = {lambda_val}")
            params = ModelParameters()
            params.lambda_risk = lambda_val
            
            solution = self._run_single_experiment(
                scenarios, params, f"lambda_{lambda_val}"
            )
            
            if solution['status'] == 'optimal':
                row = {
                    'lambda': lambda_val,
                    'objective': solution['objective_value'],
                    'var': solution['risk_metrics'].get('var', 0),
                    'cvar': solution['risk_metrics'].get('cvar', 0),
                    'expected_cost': solution['risk_metrics'].get('expected_cost', 0)
                }
                
                if 'second_stage_summary' in solution:
                    service_levels = solution['second_stage_summary'].get('service_levels', {})
                    row['avg_service_level'] = np.mean(list(service_levels.values()))
                
                results.append(row)
        
        df = pd.DataFrame(results)
        df.to_csv(self.reporter.output_dir / "lambda_sweep.csv", index=False)
        
        # Visualize sweep
        self.visualizer.plot_parameter_sweep(
            df, 'lambda',
            ['objective', 'cvar', 'avg_service_level'],
            'lambda_sweep'
        )
        
        return df
    
    def run_parameter_sweep_alpha(self, alpha_values: List[float]) -> pd.DataFrame:
        """Sweep CVaR confidence level (alpha)."""
        print(f"\nRunning alpha sweep: {alpha_values}")
        
        scenario_gen = ScenarioGenerator(self.network, self.scenario_params)
        scenarios = scenario_gen.generate_scenarios(self.base_params.num_scenarios)
        
        results = []
        for alpha_val in alpha_values:
            print(f"\nTesting alpha = {alpha_val}")
            params = ModelParameters()
            params.alpha_cvar = alpha_val
            
            solution = self._run_single_experiment(
                scenarios, params, f"alpha_{alpha_val}"
            )
            
            if solution['status'] == 'optimal':
                row = {
                    'alpha': alpha_val,
                    'objective': solution['objective_value'],
                    'cvar': solution['risk_metrics'].get('cvar', 0),
                }
                results.append(row)
        
        df = pd.DataFrame(results)
        df.to_csv(self.reporter.output_dir / "alpha_sweep.csv", index=False)
        
        self.visualizer.plot_parameter_sweep(
            df, 'alpha', ['objective', 'cvar'], 'alpha_sweep'
        )
        
        return df
    
    def run_parameter_sweep_beta(self, beta_values: List[float]) -> pd.DataFrame:
        """Sweep minimum service level (beta)."""
        print(f"\nRunning beta sweep: {beta_values}")
        
        scenario_gen = ScenarioGenerator(self.network, self.scenario_params)
        scenarios = scenario_gen.generate_scenarios(self.base_params.num_scenarios)
        
        results = []
        for beta_val in beta_values:
            print(f"\nTesting beta = {beta_val}")
            params = ModelParameters()
            params.beta_min_service = beta_val
            params.equity_mode = 1  # Use Mode 1 for beta sweep
            
            solution = self._run_single_experiment(
                scenarios, params, f"beta_{beta_val}"
            )
            
            if solution['status'] == 'optimal':
                row = {
                    'beta': beta_val,
                    'objective': solution['objective_value'],
                }
                
                if 'second_stage_summary' in solution:
                    service_levels = solution['second_stage_summary'].get('service_levels', {})
                    row['avg_service_level'] = np.mean(list(service_levels.values()))
                    row['min_service_level'] = np.min(list(service_levels.values()))
                
                results.append(row)
        
        df = pd.DataFrame(results)
        df.to_csv(self.reporter.output_dir / "beta_sweep.csv", index=False)
        
        self.visualizer.plot_parameter_sweep(
            df, 'beta', ['objective', 'avg_service_level', 'min_service_level'],
            'beta_sweep'
        )
        
        return df
    
    def run_parameter_sweep_budget(self, budget_values: List[float]) -> pd.DataFrame:
        """Sweep hardening budget."""
        print(f"\nRunning budget sweep: {budget_values}")
        
        scenario_gen = ScenarioGenerator(self.network, self.scenario_params)
        scenarios = scenario_gen.generate_scenarios(self.base_params.num_scenarios)
        
        results = []
        for budget_val in budget_values:
            print(f"\nTesting hardening budget = ${budget_val}")
            params = ModelParameters()
            params.hardening_budget = budget_val
            
            solution = self._run_single_experiment(
                scenarios, params, f"budget_{budget_val}"
            )
            
            if solution['status'] == 'optimal':
                row = {
                    'hardening_budget': budget_val,
                    'objective': solution['objective_value'],
                    'arcs_hardened': len(solution['first_stage']['hardening'])
                }
                
                if 'second_stage_summary' in solution:
                    service_levels = solution['second_stage_summary'].get('service_levels', {})
                    row['avg_service_level'] = np.mean(list(service_levels.values()))
                
                results.append(row)
        
        df = pd.DataFrame(results)
        df.to_csv(self.reporter.output_dir / "budget_sweep.csv", index=False)
        
        self.visualizer.plot_parameter_sweep(
            df, 'hardening_budget',
            ['objective', 'arcs_hardened', 'avg_service_level'],
            'budget_sweep'
        )
        
        return df
    
    def _run_single_experiment(self, scenarios, params, experiment_name):
        """Helper to run a single experiment."""
        model = WildfireSupplyNetworkModel(self.network, params, scenarios)
        pyomo_model = model.build_model()
        
        solver = OptimizationSolver()
        solution = solver.solve(pyomo_model)
        
        if solution['status'] == 'optimal':
            # Generate reports
            self.reporter.generate_summary_report(solution, experiment_name)
            self.reporter.print_summary(solution)
            
            # Generate visualizations
            self.visualizer.plot_scenario_cost_distribution(solution, experiment_name)
            self.visualizer.plot_first_stage_decisions(solution, experiment_name)
            
            if 'second_stage_summary' in solution:
                zones = list(solution['second_stage_summary']['service_levels'].keys())
                self.visualizer.plot_service_level_heatmap(solution, zones, experiment_name)
                self.visualizer.plot_fairness_analysis(solution, experiment_name)
        
        return solution
    
    def _generate_baseline_comparison(self, results: Dict[str, Any]):
        """Generate comparison report for baseline experiments."""
        experiment_names = list(results.keys())
        solutions = list(results.values())
        
        # Generate comparison table
        comparison_df = self.reporter.generate_comparison_table(solutions, experiment_names)
        
        # Generate comparison plots
        if not comparison_df.empty:
            self.visualizer.plot_comparison(comparison_df, 'Objective', 'baseline_comparison')
            if 'Avg Service' in comparison_df.columns:
                self.visualizer.plot_comparison(comparison_df, 'Avg Service', 
                                              'baseline_service_comparison')
