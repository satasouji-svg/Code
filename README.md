# Wildfire-Resilient Supply Network Optimization

A comprehensive Python project for optimizing supply network resilience against wildfire disruptions using two-stage stochastic programming with CVaR-based risk management and equity constraints.

## Overview

This project implements a sophisticated optimization framework for designing resilient supply networks that can withstand wildfire-related disruptions. The model uses:

- **Two-stage stochastic programming**: Separates strategic (first-stage) and operational (second-stage) decisions
- **CVaR risk management**: Incorporates Conditional Value-at-Risk for risk-averse decision-making
- **Equity constraints**: Ensures fair service distribution across demand zones
- **Network hardening**: Optimizes infrastructure reinforcement investments
- **Dynamic prepositioning**: Strategic inventory placement at distribution centers

## Features

### Mathematical Model
- ✅ Two-stage stochastic programming formulation
- ✅ First-stage decisions: arc hardening and inventory prepositioning
- ✅ Second-stage decisions: flows, emergency bypass, and shortages
- ✅ CVaR-based risk-averse objective function
- ✅ Flow conservation constraints at all nodes
- ✅ Supplier capacity and storage limit constraints
- ✅ Arc disruption modeling with hardening effects
- ✅ Two equity modes:
  - Mode 1: Minimum service level guarantee
  - Mode 2: Minimize service inequity across zones

### Implementation
- ✅ Pyomo-based optimization model
- ✅ HiGHS solver integration (fast open-source MIP solver)
- ✅ Modular architecture with clean separation of concerns
- ✅ Automatic scenario generation with configurable parameters
- ✅ Correlated demand and disruption modeling

### Validation & Testing
- ✅ Comprehensive test suite with pytest
- ✅ Flow conservation validation
- ✅ Probability sum verification
- ✅ Constraint satisfaction checking
- ✅ Edge case testing (high demand, zero budget, single scenario)
- ✅ CVaR calculation validation

### Experimental Design
- ✅ Baseline experiments:
  - Full model with all features
  - Risk-neutral comparison
  - No-resilience baseline
  - No-prepositioning baseline
- ✅ Parameter sweeps:
  - Lambda (risk aversion): 0.0 to 1.0
  - Alpha (CVaR confidence): 0.90, 0.95, 0.99
  - Beta (minimum service): 0.6 to 0.9
  - Hardening budget: $0 to $20,000

### Reporting & Visualization
- ✅ Paper-quality tables and figures
- ✅ Scenario cost distributions with CVaR markers
- ✅ Service level heatmaps
- ✅ Fairness analysis plots
- ✅ Parameter sensitivity charts
- ✅ First-stage decision visualizations
- ✅ Comprehensive JSON and CSV exports

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/satasouji-svg/Code.git
cd Code
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Quick Demo

Run a quick demonstration to see all features:

```bash
python main.py --mode demo
```

This will:
- Generate stochastic scenarios
- Build and solve the optimization model
- Validate the solution
- Generate reports and visualizations
- Save results to `results/` directory

### Baseline Experiments

Run comprehensive baseline comparisons:

```bash
python main.py --mode baseline
```

This compares:
- Full model (with CVaR, hardening, and prepositioning)
- Risk-neutral model (lambda=0)
- No-resilience model (no hardening)
- No-prepositioning model

### Parameter Sweeps

Run parameter sensitivity analysis:

```bash
python main.py --mode sweeps
```

This performs sweeps over:
- Risk aversion (lambda)
- CVaR confidence (alpha)
- Minimum service level (beta)
- Hardening budget

### Run Everything

To run all experiments:

```bash
python main.py --mode all
```

## Project Structure

```
Code/
├── config.py              # Configuration and parameters
├── scenario_gen.py        # Stochastic scenario generation
├── model.py              # Two-stage stochastic programming model
├── solver.py             # Solver interface (HiGHS)
├── validation.py         # Model and solution validation
├── reporter.py           # Result reporting and tables
├── visualizer.py         # Visualization and plots
├── experiments.py        # Experimental design and execution
├── main.py              # Main execution script
├── test_optimization.py  # Comprehensive test suite
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Module Documentation

### config.py
Defines network topology, costs, and model parameters:
- `NetworkConfig`: Network structure and cost parameters
- `ModelParameters`: Optimization model parameters
- `ScenarioParameters`: Scenario generation settings

### scenario_gen.py
Generates stochastic scenarios with:
- Correlated demand surges across zones
- Spatially correlated arc disruptions (wildfire modeling)
- Configurable probability distributions
- Scenario summary statistics

### model.py
Implements the two-stage stochastic programming model:
- `WildfireSupplyNetworkModel`: Main model class
- First-stage variables: hardening, prepositioning
- Second-stage variables: flows, shortages, inventory
- CVaR risk-averse objective
- Flow conservation and capacity constraints
- Equity constraints (Mode 1 or Mode 2)

### solver.py
Provides solver interface:
- `OptimizationSolver`: HiGHS solver wrapper
- Solution extraction and formatting
- Risk metrics calculation
- Time limit and gap tolerance support

### validation.py
Validates models and solutions:
- `ModelValidator`: Comprehensive validation
- Flow conservation checks
- Probability sum verification
- Constraint satisfaction validation
- CVaR calculation verification

### reporter.py
Generates result reports:
- Summary tables
- Cost breakdowns
- Service level tables
- Scenario cost distributions
- First-stage decision tables
- JSON export for further analysis

### visualizer.py
Creates paper-quality visualizations:
- Cost distribution plots with CVaR markers
- Service level heatmaps
- Fairness analysis charts
- Parameter sweep sensitivity plots
- First-stage decision visualizations
- Experiment comparison plots

### experiments.py
Orchestrates experimental design:
- `ExperimentRunner`: Experiment execution framework
- Baseline experiment suite
- Parameter sweep implementations
- Automated result generation

## Configuration

### Network Configuration

Edit `config.py` to customize:
- Suppliers, distribution centers, demand zones
- Network topology (arcs)
- Capacities and demands
- Cost parameters

### Model Parameters

Adjust in `config.py`:
```python
lambda_risk = 0.5         # Risk aversion (0=risk-neutral, 1=risk-averse)
alpha_cvar = 0.95         # CVaR confidence level
equity_mode = 1           # 1=min service, 2=min inequity
beta_min_service = 0.80   # Minimum service level (Mode 1)
hardening_budget = 15000  # Budget for arc hardening ($)
num_scenarios = 20        # Number of scenarios
```

### Scenario Generation

Customize in `config.py`:
```python
demand_correlation = 0.3      # Correlation between zone demands
disruption_prob_base = 0.15   # Base probability of arc disruption
spatial_correlation = True    # Enable wildfire spatial correlation
random_seed = 42             # For reproducibility
```

## Output Files

### Reports (CSV)
- `{experiment}_summary.csv`: High-level results
- `{experiment}_cost_breakdown.csv`: Detailed cost components
- `{experiment}_service_levels.csv`: Service by zone
- `{experiment}_scenario_costs.csv`: Cost by scenario
- `{experiment}_first_stage_decisions.csv`: Strategic decisions
- `experiment_comparison.csv`: Cross-experiment comparison

### Figures (PNG)
- `{experiment}_cost_distribution.png`: Scenario cost histogram
- `{experiment}_service_heatmap.png`: Service level heatmap
- `{experiment}_fairness_analysis.png`: Equity metrics
- `{experiment}_first_stage_decisions.png`: Hardening/prepositioning
- `{experiment}_parameter_sweep.png`: Sensitivity analysis

### Data (JSON)
- `{experiment}_solution.json`: Complete solution data

## Testing

Run the test suite:

```bash
pytest test_optimization.py -v
```

Test coverage includes:
- Configuration validation
- Scenario generation
- Model building
- Solver functionality
- Solution validation
- Edge cases (zero budget, high demand, single scenario)
- CVaR calculations
- Equity modes

## Results Interpretation

### Key Metrics

1. **Objective Value**: Total cost including first-stage and expected second-stage costs
2. **VaR (Value-at-Risk)**: Worst-case cost threshold at confidence level α
3. **CVaR (Conditional VaR)**: Expected cost in worst-case tail scenarios
4. **Service Levels**: Fraction of demand met per zone
5. **Arcs Hardened**: Number of arcs reinforced against disruptions
6. **Prepositioning**: Strategic inventory placement

### Trade-offs

- **Risk vs. Cost**: Higher λ (risk aversion) increases CVaR weight, leading to more conservative solutions
- **Resilience vs. Budget**: Higher hardening budgets improve service but increase first-stage costs
- **Equity vs. Efficiency**: Stricter equity constraints (higher β) may increase total costs
- **Prepositioning vs. Holding**: Strategic inventory reduces shortages but incurs holding costs

## Performance

- **Small instances** (3 scenarios): < 5 seconds
- **Medium instances** (20 scenarios): 10-30 seconds
- **Large instances** (50+ scenarios): 1-5 minutes

Performance depends on:
- Number of scenarios
- Network size
- Solver configuration
- Hardware specifications

## Troubleshooting

### Solver Not Found
If you get "Solver not available" errors:
```bash
pip install --upgrade highspy
```

### Infeasible Solutions
If models are infeasible:
- Check hardening budget (may be too restrictive)
- Verify supplier capacities are sufficient
- Review minimum service level constraints (β)
- Increase emergency arc availability

### Slow Performance
To improve performance:
- Reduce number of scenarios
- Increase solver time limit
- Adjust MIP gap tolerance
- Use smaller network instances

## Contributing

This is a research project. Contributions welcome:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## Citation

If you use this project in research, please cite:

```
@software{wildfire_supply_optimization,
  title={Wildfire-Resilient Supply Network Optimization},
  author={[Your Name]},
  year={2026},
  url={https://github.com/satasouji-svg/Code}
}
```

## License

This project is provided for research and educational purposes.

## References

- Rockafellar, R. T., & Uryasev, S. (2000). Optimization of conditional value-at-risk. Journal of risk, 2, 21-42.
- Birge, J. R., & Louveaux, F. (2011). Introduction to stochastic programming. Springer Science & Business Media.
- Noyan, N. (2012). Risk-averse two-stage stochastic programming with an application to disaster management. Computers & Operations Research, 39(3), 541-559.

## Contact

For questions or issues, please open an issue on GitHub.

---

**Note**: This project demonstrates advanced optimization techniques for supply chain resilience. Results should be validated with domain experts before operational deployment.