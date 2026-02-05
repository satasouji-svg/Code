# Scenarios FAQ

## How Many Scenarios Are There?

### Quick Answer

**The system uses 20 scenarios by default.**

### Detailed Information

#### Default Configuration

The default number of scenarios is defined in `config.py`:

```python
class ModelParameters:
    def __init__(self):
        # ... other parameters ...
        self.num_scenarios = 20  # Default: 20 scenarios
```

#### What is a Scenario?

A scenario represents one possible realization of uncertain events:
- **Demand surges**: How much demand increases in each zone
- **Arc disruptions**: Which transportation arcs are affected by wildfires
- **Severity levels**: How much capacity is lost on disrupted arcs

Each scenario has equal probability: `1/20 = 0.05` (5% chance)

#### Scenario Statistics (Default Configuration)

When you run the demo with 20 scenarios, you typically see:
- Total demand range: 170.0 - 236.3 tons
- Disruption range: 0 - 3 arcs affected
- Each scenario probability: 0.05 (5%)

#### How to Change the Number of Scenarios

**Method 1: Modify `config.py`**
```python
# In config.py, ModelParameters class
self.num_scenarios = 50  # Change from 20 to 50
```

**Method 2: Programmatically**
```python
from config import get_default_config

network_config, model_params, scenario_params = get_default_config()
model_params.num_scenarios = 100  # Set custom value

# Use these parameters in your optimization...
```

**Method 3: Use Examples**
```python
# In examples.py, various configurations are shown
python examples.py  # Runs with different scenario counts
```

#### Scenario Count Recommendations

| Use Case | Recommended Count | Solve Time | Accuracy |
|----------|------------------|------------|----------|
| **Quick Testing** | 3-10 scenarios | < 5 sec | Low |
| **Development** | 20 scenarios | 10-30 sec | Medium |
| **Production** | 50-100 scenarios | 1-5 min | High |
| **Research** | 100-500 scenarios | 5-30 min | Very High |

#### Impact on Performance

More scenarios = Better accuracy but longer solve time:
- **3 scenarios**: ~0.05 seconds
- **20 scenarios**: ~0.06-0.18 seconds (default)
- **50 scenarios**: ~1-2 seconds
- **100 scenarios**: ~5-10 seconds
- **500 scenarios**: ~30-60 seconds

#### Impact on Solution Quality

More scenarios provide:
- ✅ Better representation of uncertainty
- ✅ More robust first-stage decisions
- ✅ More accurate risk metrics (VaR, CVaR)
- ✅ Better coverage of extreme events

Fewer scenarios may lead to:
- ⚠️ Optimistic bias (underestimating risks)
- ⚠️ Less robust solutions
- ⚠️ Missing rare but important events

#### Checking Current Configuration

**View in Demo Output:**
```bash
python main.py --mode demo
# Look for: "Generated 20 scenarios"
```

**View in Code:**
```bash
grep "num_scenarios" config.py
# Output: self.num_scenarios = 20
```

**Run Test:**
```python
from config import get_default_config

_, model_params, _ = get_default_config()
print(f"Number of scenarios: {model_params.num_scenarios}")
# Output: Number of scenarios: 20
```

#### Related Files

- `config.py` (line 113): Default scenario count definition
- `scenario_gen.py`: Scenario generation logic
- `main.py`: Uses scenarios in optimization
- `experiments.py`: Runs experiments with scenarios

#### See Also

- [README.md](README.md) - Main documentation
- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Project overview
- [config.py](config.py) - Configuration source code

---

**Last Updated:** 2026-02-05  
**Default Scenarios:** 20  
**Configurable:** Yes ✅
