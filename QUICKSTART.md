# Quick Start Guide

This guide will help you get started with the Wildfire-Resilient Supply Network Optimization project in 5 minutes.

## Step 1: Installation (1 minute)

```bash
# Clone the repository
git clone https://github.com/satasouji-svg/Code.git
cd Code

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Run Quick Demo (1 minute)

```bash
python main.py --mode demo
```

This will:
- Generate 20 stochastic scenarios
- Build and solve the optimization model
- Validate the solution
- Create all reports and visualizations

**Expected output**: Results in `results/` directory and figures in `results/figures/`

## Step 3: View Results (1 minute)

Check the generated outputs:

```bash
# View summary report
cat results/quick_demo_summary.csv

# View service levels
cat results/quick_demo_service_levels.csv

# View figures (open in image viewer)
ls results/figures/
```

## Step 4: Run Your Own Experiments (2 minutes)

### A. Try Different Risk Levels

Edit `config.py` and change:
```python
lambda_risk = 0.8  # Increase risk aversion (0=risk-neutral, 1=risk-averse)
```

Then run:
```bash
python main.py --mode demo
```

### B. Try Different Equity Modes

Edit `config.py`:
```python
equity_mode = 1  # Mode 1: minimum service level
beta_min_service = 0.90  # 90% minimum service
```

### C. Run Baseline Comparisons

```bash
python main.py --mode baseline
```

This compares:
- Full model
- Risk-neutral (lambda=0)
- No-resilience (no hardening)
- No-prepositioning

### D. Run Parameter Sweeps

```bash
python main.py --mode sweeps
```

This performs sensitivity analysis on:
- Lambda (risk aversion)
- Alpha (CVaR confidence)
- Beta (minimum service)
- Hardening budget

## Step 5: Run Custom Examples

Try pre-built custom configurations:

```bash
python examples.py
```

This runs 5 different scenarios:
1. High risk aversion
2. Equity-focused
3. Large network
4. High disruption
5. Cost minimization

## Understanding the Results

### Key Metrics

1. **Objective Value**: Total expected cost
2. **VaR**: Value at Risk (threshold cost)
3. **CVaR**: Conditional VaR (tail risk)
4. **Service Levels**: % of demand met per zone
5. **Arcs Hardened**: Number of reinforced arcs

### Output Files

**CSV Reports**:
- `*_summary.csv`: High-level metrics
- `*_service_levels.csv`: Service by zone
- `*_cost_breakdown.csv`: Cost components
- `*_scenario_costs.csv`: Cost by scenario
- `*_first_stage_decisions.csv`: Strategic decisions

**Visualizations**:
- `*_cost_distribution.png`: Scenario cost histogram
- `*_service_heatmap.png`: Service levels by zone
- `*_fairness_analysis.png`: Equity metrics
- `*_first_stage_decisions.png`: Investment decisions

## Customization Quick Reference

### Change Network Size

In `config.py`:
```python
self.suppliers = ['S1', 'S2', 'S3', 'S4']  # Add more suppliers
self.demand_zones = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5']  # Add more zones
```

### Change Risk Parameters

In `config.py`:
```python
self.lambda_risk = 0.5  # Risk aversion [0, 1]
self.alpha_cvar = 0.95  # CVaR confidence [0.90, 0.95, 0.99]
```

### Change Scenario Count

In `config.py`:
```python
self.num_scenarios = 50  # More scenarios = more accurate but slower
```

### Change Hardening Budget

In `config.py`:
```python
self.hardening_budget = 20000.0  # Higher budget = more resilience
```

## Running Tests

Verify everything works:

```bash
pytest test_optimization.py -v
```

Expected: All 24 tests should pass.

## Troubleshooting

### Problem: Solver not found
**Solution**: 
```bash
pip install --upgrade highspy
```

### Problem: Infeasible model
**Solution**: 
- Increase hardening budget
- Reduce minimum service level (beta)
- Check supplier capacities are sufficient

### Problem: Slow solving
**Solution**:
- Reduce number of scenarios
- Use smaller network
- Increase time limit in solver options

## Next Steps

1. **Read the full README.md** for comprehensive documentation
2. **Explore `examples.py`** for advanced configurations
3. **Modify `config.py`** to match your specific network
4. **Run parameter sweeps** to understand trade-offs
5. **Customize visualizations** in `visualizer.py`

## Common Use Cases

### Use Case 1: Evaluate Hardening Investment

```bash
# Run budget sweep
python main.py --mode sweeps
# Check budget_sweep.csv and budget_sweep_*.png
```

### Use Case 2: Compare Risk Strategies

```bash
# Run lambda sweep
python main.py --mode sweeps
# Check lambda_sweep.csv and lambda_sweep_*.png
```

### Use Case 3: Ensure Fair Service

```python
# In config.py, set:
equity_mode = 1
beta_min_service = 0.90

# Then run:
python main.py --mode demo
```

## Support

- **Documentation**: See README.md
- **Examples**: See examples.py
- **Tests**: See test_optimization.py
- **Issues**: Open an issue on GitHub

---

**Tip**: Start with the quick demo, then gradually customize parameters to match your specific use case!
