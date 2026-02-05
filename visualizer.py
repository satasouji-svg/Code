"""
Visualization module for creating paper-quality plots and figures.
Includes scenario cost distributions, fairness heatmaps, and sensitivity analysis.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from pathlib import Path


class ResultVisualizer:
    """Create visualizations for optimization results."""
    
    def __init__(self, output_dir: str = "results/figures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set publication-quality style
        plt.style.use('seaborn-v0_8-paper')
        sns.set_palette("husl")
    
    def plot_scenario_cost_distribution(self, solution: Dict[str, Any],
                                       experiment_name: str = "default",
                                       figsize: tuple = (10, 6)):
        """Plot distribution of scenario costs with CVaR visualization."""
        
        if solution['status'] != 'optimal' or 'second_stage_summary' not in solution:
            print("Cannot plot: solution not optimal or missing data")
            return
        
        scenario_costs = solution['second_stage_summary'].get('scenario_costs', {})
        if not scenario_costs:
            print("No scenario cost data available")
            return
        
        costs = list(scenario_costs.values())
        scenarios = list(scenario_costs.keys())
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Histogram with CVaR threshold
        ax1.hist(costs, bins=15, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(np.mean(costs), color='green', linestyle='--', 
                   linewidth=2, label=f'Mean: ${np.mean(costs):,.0f}')
        
        if 'risk_metrics' in solution and solution['risk_metrics'].get('var'):
            var_value = solution['risk_metrics']['var']
            ax1.axvline(var_value, color='orange', linestyle='--',
                       linewidth=2, label=f'VaR (95%): ${var_value:,.0f}')
        
        if 'risk_metrics' in solution and solution['risk_metrics'].get('cvar'):
            cvar_value = solution['risk_metrics']['cvar']
            ax1.axvline(cvar_value, color='red', linestyle='--',
                       linewidth=2, label=f'CVaR (95%): ${cvar_value:,.0f}')
        
        ax1.set_xlabel('Scenario Cost ($)', fontsize=12)
        ax1.set_ylabel('Frequency', fontsize=12)
        ax1.set_title('Scenario Cost Distribution', fontsize=14, fontweight='bold')
        ax1.legend(fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # Sorted cost plot
        sorted_costs = sorted(costs)
        ax2.plot(scenarios, sorted_costs, marker='o', linewidth=2, markersize=6)
        ax2.axhline(np.mean(costs), color='green', linestyle='--', 
                   linewidth=2, alpha=0.7)
        ax2.fill_between(range(len(scenarios)), 
                        sorted_costs,
                        alpha=0.3, color='skyblue')
        ax2.set_xlabel('Scenario (sorted by cost)', fontsize=12)
        ax2.set_ylabel('Cost ($)', fontsize=12)
        ax2.set_title('Scenario Costs (Sorted)', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save figure
        output_file = self.output_dir / f"{experiment_name}_cost_distribution.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Cost distribution plot saved to {output_file}")
        plt.close()
    
    def plot_service_level_heatmap(self, solution: Dict[str, Any],
                                   zones: List[str],
                                   experiment_name: str = "default",
                                   figsize: tuple = (10, 6)):
        """Create heatmap of service levels across zones."""
        
        if solution['status'] != 'optimal' or 'second_stage_summary' not in solution:
            print("Cannot plot: solution not optimal or missing data")
            return
        
        service_levels = solution['second_stage_summary'].get('service_levels', {})
        if not service_levels:
            print("No service level data available")
            return
        
        # Create data matrix
        data = [[service_levels.get(zone, 0) * 100] for zone in zones]
        
        fig, ax = plt.subplots(figsize=figsize)
        
        # Create heatmap
        sns.heatmap(data, annot=True, fmt='.1f', cmap='RdYlGn', vmin=0, vmax=100,
                   cbar_kws={'label': 'Service Level (%)'},
                   yticklabels=zones, xticklabels=['Service Level'],
                   linewidths=0.5, linecolor='gray', ax=ax)
        
        ax.set_title('Service Level by Demand Zone', fontsize=14, fontweight='bold')
        ax.set_ylabel('Demand Zone', fontsize=12)
        
        plt.tight_layout()
        
        # Save figure
        output_file = self.output_dir / f"{experiment_name}_service_heatmap.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Service level heatmap saved to {output_file}")
        plt.close()
    
    def plot_fairness_analysis(self, solution: Dict[str, Any],
                              experiment_name: str = "default",
                              figsize: tuple = (10, 6)):
        """Analyze and visualize equity/fairness metrics."""
        
        if solution['status'] != 'optimal' or 'second_stage_summary' not in solution:
            return
        
        service_levels = solution['second_stage_summary'].get('service_levels', {})
        if not service_levels:
            return
        
        zones = list(service_levels.keys())
        levels = [service_levels[z] * 100 for z in zones]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Bar chart of service levels
        colors = ['green' if l >= 80 else 'orange' if l >= 60 else 'red' for l in levels]
        ax1.bar(zones, levels, color=colors, alpha=0.7, edgecolor='black')
        ax1.axhline(80, color='green', linestyle='--', linewidth=2, 
                   label='Target: 80%', alpha=0.7)
        ax1.set_xlabel('Demand Zone', fontsize=12)
        ax1.set_ylabel('Service Level (%)', fontsize=12)
        ax1.set_title('Service Level by Zone', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')
        ax1.set_ylim([0, 105])
        
        # Equity metrics
        mean_service = np.mean(levels)
        std_service = np.std(levels)
        min_service = np.min(levels)
        max_service = np.max(levels)
        range_service = max_service - min_service
        
        metrics_text = (
            f"Mean Service: {mean_service:.1f}%\n"
            f"Std Dev: {std_service:.1f}%\n"
            f"Min: {min_service:.1f}%\n"
            f"Max: {max_service:.1f}%\n"
            f"Range: {range_service:.1f}%"
        )
        
        ax2.text(0.1, 0.5, metrics_text, fontsize=14,
                verticalalignment='center', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        ax2.set_xlim([0, 1])
        ax2.set_ylim([0, 1])
        ax2.axis('off')
        ax2.set_title('Equity Metrics', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Save figure
        output_file = self.output_dir / f"{experiment_name}_fairness_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Fairness analysis saved to {output_file}")
        plt.close()
    
    def plot_parameter_sweep(self, sweep_results: pd.DataFrame,
                           param_name: str,
                           metrics: List[str],
                           experiment_name: str = "default",
                           figsize: tuple = (12, 8)):
        """Plot results from parameter sweep experiments."""
        
        if sweep_results.empty:
            print("No sweep results to plot")
            return
        
        n_metrics = len(metrics)
        fig, axes = plt.subplots(n_metrics, 1, figsize=figsize, sharex=True)
        
        if n_metrics == 1:
            axes = [axes]
        
        for idx, metric in enumerate(metrics):
            if metric in sweep_results.columns:
                axes[idx].plot(sweep_results[param_name], sweep_results[metric],
                             marker='o', linewidth=2, markersize=8)
                axes[idx].set_ylabel(metric, fontsize=12)
                axes[idx].grid(True, alpha=0.3)
                axes[idx].set_title(f'{metric} vs {param_name}', 
                                   fontsize=12, fontweight='bold')
        
        axes[-1].set_xlabel(param_name, fontsize=12)
        
        plt.tight_layout()
        
        # Save figure
        output_file = self.output_dir / f"{experiment_name}_parameter_sweep.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Parameter sweep plot saved to {output_file}")
        plt.close()
    
    def plot_first_stage_decisions(self, solution: Dict[str, Any],
                                   experiment_name: str = "default",
                                   figsize: tuple = (12, 6)):
        """Visualize first-stage decisions: hardening and prepositioning."""
        
        if solution['status'] != 'optimal' or 'first_stage' not in solution:
            return
        
        first_stage = solution['first_stage']
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        
        # Hardening decisions
        hardened_arcs = list(first_stage['hardening'].keys())
        if hardened_arcs:
            arc_labels = [f"{arc[0]}-{arc[1]}" for arc in hardened_arcs]
            ax1.barh(arc_labels, [1]*len(hardened_arcs), color='steelblue', alpha=0.7)
            ax1.set_xlabel('Hardened (Yes/No)', fontsize=12)
            ax1.set_ylabel('Arc', fontsize=12)
            ax1.set_title('Hardening Decisions', fontsize=14, fontweight='bold')
            ax1.set_xlim([0, 1.5])
        else:
            ax1.text(0.5, 0.5, 'No arcs hardened', ha='center', va='center',
                    fontsize=12, transform=ax1.transAxes)
            ax1.set_title('Hardening Decisions', fontsize=14, fontweight='bold')
        
        # Prepositioning decisions
        prepos = first_stage['prepositioning']
        if prepos:
            dcs = list(prepos.keys())
            amounts = list(prepos.values())
            colors = plt.cm.viridis(np.linspace(0, 1, len(dcs)))
            ax2.bar(dcs, amounts, color=colors, alpha=0.7, edgecolor='black')
            ax2.set_xlabel('Distribution Center', fontsize=12)
            ax2.set_ylabel('Prepositioning Amount', fontsize=12)
            ax2.set_title('Prepositioning Decisions', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')
        else:
            ax2.text(0.5, 0.5, 'No prepositioning', ha='center', va='center',
                    fontsize=12, transform=ax2.transAxes)
            ax2.set_title('Prepositioning Decisions', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Save figure
        output_file = self.output_dir / f"{experiment_name}_first_stage_decisions.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"First-stage decisions plot saved to {output_file}")
        plt.close()
    
    def plot_comparison(self, comparison_df: pd.DataFrame,
                       metric: str,
                       experiment_name: str = "comparison",
                       figsize: tuple = (10, 6)):
        """Create comparison plots across experiments."""
        
        if comparison_df.empty or metric not in comparison_df.columns:
            return
        
        fig, ax = plt.subplots(figsize=figsize)
        
        experiments = comparison_df['Experiment'].tolist()
        values = comparison_df[metric].tolist()
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(experiments)))
        bars = ax.bar(experiments, values, color=colors, alpha=0.7, edgecolor='black')
        
        ax.set_xlabel('Experiment', fontsize=12)
        ax.set_ylabel(metric, fontsize=12)
        ax.set_title(f'{metric} Comparison', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.2f}',
                   ha='center', va='bottom', fontsize=10)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save figure
        output_file = self.output_dir / f"{experiment_name}_{metric.replace(' ', '_')}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Comparison plot saved to {output_file}")
        plt.close()
