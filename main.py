"""
Main execution script for wildfire-resilient supply network optimization.

This script orchestrates the complete optimization pipeline including:
1. Configuration and validation
2. Scenario generation
3. Model building and solving
4. Results reporting and visualization
"""

import sys
import argparse
from typing import Optional

# Import all modules
from config import Config, get_default_config
from scenario_generator import generate_scenarios
from data_validator import validate_data
from optimization_model import TwoStageStochasticModel
from reporter import print_summary, Reporter
from visualizer import create_visualizations


def run_optimization(config: Optional[Config] = None, 
                    output_dir: str = "results",
                    save_report: bool = True,
                    create_plots: bool = True) -> dict:
    """
    Run the complete optimization pipeline.
    
    Args:
        config: Configuration object (uses default if None)
        output_dir: Directory for outputs
        save_report: Whether to save detailed report
        create_plots: Whether to create visualizations
        
    Returns:
        Dictionary containing results and metadata
    """
    print("\n" + "="*80)
    print("WILDFIRE-RESILIENT SUPPLY NETWORK OPTIMIZATION")
    print("="*80 + "\n")
    
    # Step 1: Configuration
    print("📋 Step 1: Loading Configuration")
    if config is None:
        config = get_default_config()
    print(f"   ✅ Configuration loaded")
    print(f"      Network: {len(config.network.suppliers)} suppliers, "
          f"{len(config.network.distribution_centers)} DCs, "
          f"{len(config.network.demand_nodes)} demand nodes")
    print(f"      Scenarios: {config.scenario.n_scenarios}")
    print()
    
    # Step 2: Scenario Generation
    print("🎲 Step 2: Generating Scenarios")
    scenarios = generate_scenarios(config)
    print(f"   ✅ Generated {len(scenarios)} scenarios")
    print()
    
    # Step 3: Data Validation
    print("✓ Step 3: Validating Data")
    if not validate_data(config, scenarios):
        print("   ❌ Validation failed. Aborting.")
        sys.exit(1)
    print()
    
    # Step 4: Model Building
    print("🔧 Step 4: Building Optimization Model")
    model = TwoStageStochasticModel(config, scenarios)
    model.build_model()
    print()
    
    # Step 5: Solving
    print("⚡ Step 5: Solving Model")
    result = model.solve()
    print()
    
    # Check if solution is optimal
    if result.status != "Optimal":
        print(f"   ⚠️  Warning: Solution status is {result.status}")
        print("      Results may not be reliable.")
        print()
    
    # Step 6: Reporting
    print("📊 Step 6: Generating Reports")
    print_summary(config, scenarios, result)
    
    if save_report:
        import os
        os.makedirs(output_dir, exist_ok=True)
        reporter = Reporter(config, scenarios, result)
        report_file = f"{output_dir}/optimization_report.txt"
        reporter.save_report(report_file)
    print()
    
    # Step 7: Visualization
    if create_plots:
        print("📈 Step 7: Creating Visualizations")
        try:
            create_visualizations(config, scenarios, result, output_dir)
        except Exception as e:
            print(f"   ⚠️  Warning: Visualization failed: {e}")
            print("      Continuing without plots.")
        print()
    
    print("="*80)
    print("✅ OPTIMIZATION COMPLETED SUCCESSFULLY")
    print("="*80 + "\n")
    
    # Return results
    return {
        'config': config,
        'scenarios': scenarios,
        'result': result,
        'output_dir': output_dir
    }


def main():
    """Main entry point with command-line interface."""
    parser = argparse.ArgumentParser(
        description='Wildfire-Resilient Supply Network Optimization',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default configuration
  python main.py
  
  # Run with custom number of scenarios
  python main.py --scenarios 20
  
  # Run with custom CVaR settings
  python main.py --cvar-alpha 0.90 --cvar-weight 0.5
  
  # Run without visualizations (faster)
  python main.py --no-plots
        """
    )
    
    # Configuration arguments
    parser.add_argument('--scenarios', type=int, default=10,
                       help='Number of scenarios to generate (default: 10)')
    parser.add_argument('--cvar-alpha', type=float, default=0.95,
                       help='CVaR confidence level (default: 0.95)')
    parser.add_argument('--cvar-weight', type=float, default=0.3,
                       help='Weight of CVaR in objective (default: 0.3)')
    parser.add_argument('--min-satisfaction', type=float, default=0.75,
                       help='Minimum demand satisfaction ratio (default: 0.75)')
    parser.add_argument('--output-dir', type=str, default='results',
                       help='Output directory for results (default: results)')
    parser.add_argument('--no-report', action='store_true',
                       help='Skip saving detailed report')
    parser.add_argument('--no-plots', action='store_true',
                       help='Skip creating visualizations')
    parser.add_argument('--seed', type=int, default=42,
                       help='Random seed for reproducibility (default: 42)')
    
    args = parser.parse_args()
    
    # Create custom configuration
    config = get_default_config()
    
    # Update with command-line arguments
    config.scenario.n_scenarios = args.scenarios
    config.scenario.random_seed = args.seed
    config.optimization.cvar_alpha = args.cvar_alpha
    config.optimization.cvar_weight = args.cvar_weight
    config.optimization.expectation_weight = 1.0 - args.cvar_weight
    config.optimization.min_demand_satisfaction = args.min_satisfaction
    
    # Validate configuration
    try:
        config.validate()
    except AssertionError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Run optimization
    try:
        results = run_optimization(
            config=config,
            output_dir=args.output_dir,
            save_report=not args.no_report,
            create_plots=not args.no_plots
        )
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during optimization: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
