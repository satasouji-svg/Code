# Migration Guide: Fixing Common Issues from Custom Implementations

If you're experiencing errors when running custom implementations based on this project, this guide will help you migrate to the stable repository version or fix common issues.

## Common Issue: NameError for undefined variables

### Issue Pattern
```
NameError: name 'scenario_emergency_procurement' is not defined
NameError: name 'scenario_xxx' is not defined
```

### Why This Happens
- Variables are referenced in result extraction before being initialized
- Data structures are built in wrong order
- Variable scope issues in class methods

### Generic Fix Template

When you see `NameError: name 'variable_name' is not defined`:

1. **Find where it's used** - Look at the line number in the error
2. **Determine what it should contain** - Check surrounding code
3. **Initialize before use** - Add initialization code before the line

Example pattern:
```python
# ❌ WRONG - Using before defining
for s in scenarios:
    value = my_data[s]  # NameError if my_data not defined

# ✅ CORRECT - Define before using
my_data = {}
for s in scenarios:
    my_data[s] = calculate_something(s)

for s in scenarios:
    value = my_data[s]  # Now it works
```

## Specific Fixes for This Project

### 1. Missing scenario_emergency_procurement

**Error:**
```python
emergency = scenario_emergency_procurement[s].get(supplier, 0.0)
# NameError: name 'scenario_emergency_procurement' is not defined
```

**Fix:** Add before the line that uses it:
```python
# Initialize emergency procurement data
scenario_emergency_procurement = {}
for s in model.SCENARIOS:
    scenario_emergency_procurement[s] = {}
    for supplier in model.SUPPLIERS:
        total = sum(pyo.value(model.flow_emergency[s, arc]) 
                   for arc in model.EMERGENCY_ARCS if arc[0] == supplier)
        scenario_emergency_procurement[s][supplier] = total
```

### 2. Missing scenario costs/flows

**Pattern:**
```python
cost = scenario_costs[s]  # NameError
```

**Fix:**
```python
# Calculate and store costs first
scenario_costs = {}
for s in model.SCENARIOS:
    cost = 0
    # Add all cost components
    for arc in model.SUPPLIER_DC_ARCS:
        cost += pyo.value(model.transport_cost[arc] * model.flow_supplier_dc[s, arc])
    # ... add other costs
    scenario_costs[s] = cost
```

### 3. Missing data extraction dictionaries

**General pattern for any missing data structure:**

```python
def _extract_results(self, status, solve_time):
    """Extract results with all data structures initialized."""
    
    # STEP 1: Initialize all data structures FIRST
    results = {
        'status': status,
        'solve_time': solve_time,
        'objective': pyo.value(self.model.objective),
        'first_stage': {},
        'second_stage': {},
        'scenarios': {}
    }
    
    # STEP 2: Extract first-stage decisions
    results['first_stage']['hardening'] = {
        arc: pyo.value(self.model.harden[arc])
        for arc in self.model.HARDENABLE_ARCS
        if pyo.value(self.model.harden[arc]) > 0.5
    }
    
    results['first_stage']['prepositioning'] = {
        dc: pyo.value(self.model.preposition[dc])
        for dc in self.model.DCS
        if pyo.value(self.model.preposition[dc]) > 0.01
    }
    
    # STEP 3: Extract second-stage data for each scenario
    for s in self.model.SCENARIOS:
        scenario_data = {}
        
        # Flows
        scenario_data['flows'] = {}
        for arc in self.model.SUPPLIER_DC_ARCS:
            scenario_data['flows'][arc] = pyo.value(self.model.flow_supplier_dc[s, arc])
        
        # Emergency procurement
        scenario_data['emergency'] = {}
        for supplier in self.model.SUPPLIERS:
            total = sum(pyo.value(self.model.flow_emergency[s, arc])
                       for arc in self.model.EMERGENCY_ARCS if arc[0] == supplier)
            scenario_data['emergency'][supplier] = total
        
        # Shortages
        scenario_data['shortages'] = {
            zone: pyo.value(self.model.shortage[s, zone])
            for zone in self.model.ZONES
        }
        
        results['scenarios'][s] = scenario_data
    
    return results
```

## Best Practices to Avoid These Errors

### 1. Initialize Before Use
```python
# Always initialize dictionaries/lists before accessing
data = {}  # or []
# Then populate
data[key] = value
```

### 2. Use Default Values
```python
# Use .get() with defaults
value = dictionary.get(key, default_value)

# Or use defaultdict
from collections import defaultdict
data = defaultdict(dict)
```

### 3. Check Existence
```python
# Check if variable/attribute exists
if hasattr(object, 'attribute'):
    value = object.attribute

# Check if key exists
if key in dictionary:
    value = dictionary[key]
```

### 4. Defensive Programming
```python
try:
    value = risky_operation()
except (KeyError, NameError, AttributeError) as e:
    print(f"Warning: {e}, using default")
    value = default_value
```

### 5. Structured Extraction
```python
def extract_all_data(self):
    """Extract with clear structure."""
    # Stage 1: Initialize
    data = self._initialize_data_structures()
    
    # Stage 2: Extract first-stage
    data['first_stage'] = self._extract_first_stage()
    
    # Stage 3: Extract second-stage
    data['second_stage'] = self._extract_second_stage()
    
    # Stage 4: Calculate metrics
    data['metrics'] = self._calculate_metrics(data)
    
    return data
```

## Quick Debugging Checklist

When you get a NameError:

- [ ] Is the variable defined before the line that uses it?
- [ ] Is it in the correct scope (local vs instance variable)?
- [ ] Is it spelled correctly (typos)?
- [ ] Is it defined in ALL code paths (if/else branches)?
- [ ] Is it defined before any loop that uses it?
- [ ] Does the model have the attribute (use `hasattr()`)?
- [ ] Was the model solved successfully before extraction?

## Migration to Repository Version

If you're having multiple issues, consider using the tested repository version:

### Step 1: Backup Your Code
```bash
cp -r your_project your_project_backup
```

### Step 2: Download Repository Version
```bash
git clone https://github.com/satasouji-svg/Code.git
cd Code
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Test Repository Version
```bash
python main.py --mode demo
pytest test_optimization.py -v
```

### Step 5: Migrate Your Customizations

If you have custom modifications:

1. Copy your `config.py` changes
2. Copy your network topology modifications
3. Copy any custom scenarios
4. Test incrementally after each change

### Step 6: Run Your Scenarios

```bash
python main.py --mode demo  # Test with demo
python examples.py          # Test with examples
# Then try your custom scenarios
```

## Still Having Issues?

### Option 1: Use the Debugger
```python
# Add at the problematic line
import pdb; pdb.set_trace()
# Then inspect variables: print(dir()), print(locals())
```

### Option 2: Add Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Add logs before problematic sections
logger.info(f"Variables available: {list(locals().keys())}")
```

### Option 3: Simplify and Test
- Start with the working repository version
- Add your changes one at a time
- Test after each change
- Identify which change causes the error

## Examples of Fixed Code

See the repository files for working examples:
- `model.py` - Clean model definition
- `solver.py` - Proper result extraction
- `examples.py` - Various working scenarios

## Support

- Read: `README.md` for full documentation
- See: `BUGFIX_EMERGENCY_PROCUREMENT.md` for specific fix
- Check: `test_optimization.py` for testing patterns
- Review: `PROJECT_SUMMARY.md` for architecture overview

---

**Key Takeaway**: Always initialize data structures before using them, and extract data in a logical order (first-stage → second-stage → metrics).
