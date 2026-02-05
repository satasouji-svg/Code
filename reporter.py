"""
Reporter module for generating result summaries and tables.
Produces paper-quality outputs for analysis and publication.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import json
from pathlib import Path


class ResultReporter:
    """Generate reports and tables from optimization results."""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_summary_report(self, solution: Dict[str, Any], 
                               experiment_name: str = "default") -> pd.DataFrame:
        """Generate summary report of optimization results."""
        
        if solution['status'] != 'optimal':
            print(f"Warning: Solution status is {solution['status']}")
            return pd.DataFrame()
        
        summary_data = {
            'Experiment': experiment_name,
            'Status': solution['status'],
            'Objective Value': solution['objective_value'],
            'Solve Time (s)': solution['solve_time'],
            'Solver': solution['solver']
        }
        
        # Add risk metrics
        if 'risk_metrics' in solution:
            summary_data['VaR'] = solution['risk_metrics'].get('var', 'N/A')
            summary_data['CVaR'] = solution['risk_metrics'].get('cvar', 'N/A')
            summary_data['Expected Cost'] = solution['risk_metrics'].get('expected_cost', 'N/A')
        
        # Add first-stage costs
        if 'first_stage' in solution:
            num_hardened = len(solution['first_stage']['hardening'])
            total_preposition = sum(solution['first_stage']['prepositioning'].values())
            summary_data['Arcs Hardened'] = num_hardened
            summary_data['Total Prepositioning'] = total_preposition
        
        # Service level statistics
        if 'second_stage_summary' in solution:
            service_levels = solution['second_stage_summary'].get('service_levels', {})
            if service_levels:
                summary_data['Avg Service Level'] = np.mean(list(service_levels.values()))
                summary_data['Min Service Level'] = np.min(list(service_levels.values()))
                summary_data['Max Service Level'] = np.max(list(service_levels.values()))
        
        df = pd.DataFrame([summary_data])
        
        # Save to file
        output_file = self.output_dir / f"{experiment_name}_summary.csv"
        df.to_csv(output_file, index=False)
        print(f"Summary report saved to {output_file}")
        
        return df
    
    def generate_cost_breakdown(self, solution: Dict[str, Any],
                               experiment_name: str = "default") -> pd.DataFrame:
        """Generate detailed cost breakdown by component."""
        
        if solution['status'] != 'optimal':
            return pd.DataFrame()
        
        cost_data = []
        
        # First-stage costs (estimated from solution)
        if 'first_stage' in solution:
            first_stage = solution['first_stage']
            
            # Hardening costs
            num_hardened = len(first_stage['hardening'])
            cost_data.append({
                'Component': 'Hardening',
                'Stage': 'First',
                'Value': num_hardened * 3000  # Approximate
            })
            
            # Prepositioning costs
            total_prepos = sum(first_stage['prepositioning'].values())
            cost_data.append({
                'Component': 'Prepositioning',
                'Stage': 'First',
                'Value': total_prepos * 2.0  # Approximate cost per unit
            })
        
        # Second-stage costs
        if 'risk_metrics' in solution:
            expected_cost = solution['risk_metrics'].get('expected_cost', 0)
            cost_data.append({
                'Component': 'Expected Operations',
                'Stage': 'Second',
                'Value': expected_cost
            })
        
        df = pd.DataFrame(cost_data)
        
        # Save to file
        output_file = self.output_dir / f"{experiment_name}_cost_breakdown.csv"
        df.to_csv(output_file, index=False)
        print(f"Cost breakdown saved to {output_file}")
        
        return df
    
    def generate_service_level_table(self, solution: Dict[str, Any],
                                    experiment_name: str = "default") -> pd.DataFrame:
        """Generate table of service levels by demand zone."""
        
        if solution['status'] != 'optimal' or 'second_stage_summary' not in solution:
            return pd.DataFrame()
        
        service_levels = solution['second_stage_summary'].get('service_levels', {})
        avg_shortages = solution['second_stage_summary'].get('average_shortage', {})
        
        data = []
        for zone in service_levels.keys():
            data.append({
                'Zone': zone,
                'Service Level': service_levels[zone],
                'Average Shortage': avg_shortages.get(zone, 0),
                'Percent Served': service_levels[zone] * 100
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values('Service Level', ascending=False)
        
        # Save to file
        output_file = self.output_dir / f"{experiment_name}_service_levels.csv"
        df.to_csv(output_file, index=False)
        print(f"Service level table saved to {output_file}")
        
        return df
    
    def generate_scenario_cost_table(self, solution: Dict[str, Any],
                                    experiment_name: str = "default") -> pd.DataFrame:
        """Generate table of costs by scenario."""
        
        if solution['status'] != 'optimal' or 'second_stage_summary' not in solution:
            return pd.DataFrame()
        
        scenario_costs = solution['second_stage_summary'].get('scenario_costs', {})
        
        data = []
        for scenario_id, cost in scenario_costs.items():
            data.append({
                'Scenario': scenario_id,
                'Cost': cost
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values('Cost', ascending=False)
        
        # Add statistics
        df['Percentile'] = df['Cost'].rank(pct=True) * 100
        
        # Save to file
        output_file = self.output_dir / f"{experiment_name}_scenario_costs.csv"
        df.to_csv(output_file, index=False)
        print(f"Scenario cost table saved to {output_file}")
        
        return df
    
    def generate_first_stage_decisions_table(self, solution: Dict[str, Any],
                                            experiment_name: str = "default") -> pd.DataFrame:
        """Generate detailed table of first-stage decisions."""
        
        if solution['status'] != 'optimal' or 'first_stage' not in solution:
            return pd.DataFrame()
        
        first_stage = solution['first_stage']
        
        # Hardening decisions
        hardening_data = []
        for arc in first_stage['hardening'].keys():
            hardening_data.append({
                'Decision Type': 'Hardening',
                'Location/Arc': str(arc),
                'Value': 1
            })
        
        # Prepositioning decisions
        prepos_data = []
        for dc, amount in first_stage['prepositioning'].items():
            prepos_data.append({
                'Decision Type': 'Prepositioning',
                'Location/Arc': dc,
                'Value': amount
            })
        
        df = pd.DataFrame(hardening_data + prepos_data)
        
        # Save to file
        output_file = self.output_dir / f"{experiment_name}_first_stage_decisions.csv"
        df.to_csv(output_file, index=False)
        print(f"First-stage decisions saved to {output_file}")
        
        return df
    
    def generate_comparison_table(self, results: List[Dict[str, Any]],
                                 experiment_names: List[str]) -> pd.DataFrame:
        """Generate comparison table across multiple experiments."""
        
        comparison_data = []
        
        for result, name in zip(results, experiment_names):
            if result['status'] != 'optimal':
                continue
            
            row = {
                'Experiment': name,
                'Objective': result['objective_value'],
                'Solve Time': result['solve_time'],
            }
            
            if 'risk_metrics' in result:
                row['VaR'] = result['risk_metrics'].get('var', 'N/A')
                row['CVaR'] = result['risk_metrics'].get('cvar', 'N/A')
            
            if 'second_stage_summary' in result:
                service_levels = result['second_stage_summary'].get('service_levels', {})
                if service_levels:
                    row['Avg Service'] = np.mean(list(service_levels.values()))
            
            if 'first_stage' in result:
                row['Arcs Hardened'] = len(result['first_stage']['hardening'])
            
            comparison_data.append(row)
        
        df = pd.DataFrame(comparison_data)
        
        # Save to file
        output_file = self.output_dir / "experiment_comparison.csv"
        df.to_csv(output_file, index=False)
        print(f"Comparison table saved to {output_file}")
        
        return df
    
    def save_solution_json(self, solution: Dict[str, Any],
                          experiment_name: str = "default"):
        """Save complete solution as JSON for further analysis."""
        output_file = self.output_dir / f"{experiment_name}_solution.json"
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_types(item) for item in obj]
            else:
                return obj
        
        solution_converted = convert_types(solution)
        
        with open(output_file, 'w') as f:
            json.dump(solution_converted, f, indent=2)
        
        print(f"Solution JSON saved to {output_file}")
    
    def print_summary(self, solution: Dict[str, Any]):
        """Print a formatted summary to console."""
        print("\n" + "="*60)
        print("OPTIMIZATION RESULTS SUMMARY")
        print("="*60)
        
        print(f"Status: {solution['status']}")
        print(f"Solve Time: {solution['solve_time']:.2f} seconds")
        
        if solution['status'] == 'optimal':
            print(f"Objective Value: ${solution['objective_value']:,.2f}")
            
            if 'risk_metrics' in solution:
                print(f"\nRisk Metrics:")
                print(f"  VaR: ${solution['risk_metrics'].get('var', 'N/A'):,.2f}")
                print(f"  CVaR: ${solution['risk_metrics'].get('cvar', 'N/A'):,.2f}")
                print(f"  Expected Cost: ${solution['risk_metrics'].get('expected_cost', 'N/A'):,.2f}")
            
            if 'first_stage' in solution:
                print(f"\nFirst-Stage Decisions:")
                print(f"  Arcs Hardened: {len(solution['first_stage']['hardening'])}")
                total_prepos = sum(solution['first_stage']['prepositioning'].values())
                print(f"  Total Prepositioning: {total_prepos:.2f} units")
            
            if 'second_stage_summary' in solution:
                service_levels = solution['second_stage_summary'].get('service_levels', {})
                if service_levels:
                    print(f"\nService Levels:")
                    for zone, level in service_levels.items():
                        print(f"  {zone}: {level*100:.1f}%")
        
        print("="*60 + "\n")
