# Fix for NameError: scenario_emergency_procurement not defined

## Problem
When running the optimization model, you encounter:
```
NameError: name 'scenario_emergency_procurement' is not defined
```

This error occurs at line 878 in `optimization_model.py` in the `_extract_results` method:
```python
emergency = scenario_emergency_procurement[s].get(supplier, 0.0)
```

## Root Cause
The variable `scenario_emergency_procurement` is being referenced but was never defined or initialized in the current scope.

## Solution

### Option 1: Define the Missing Variable

Before the line where the error occurs (around line 878), you need to extract the emergency procurement data. Add this code:

```python
# Extract emergency procurement for each scenario
scenario_emergency_procurement = {}
for s in self.model.SCENARIOS:
    scenario_emergency_procurement[s] = {}
    for supplier in self.model.SUPPLIERS:
        # Sum all emergency flows from this supplier across all emergency arcs
        emergency_total = 0
        for arc in self.model.EMERGENCY_ARCS:
            if arc[0] == supplier:  # If this supplier is the source
                emergency_total += pyo.value(self.model.flow_emergency[s, arc])
        scenario_emergency_procurement[s][supplier] = emergency_total
```

### Option 2: Inline the Calculation

Instead of referencing a pre-defined variable, calculate it inline:

```python
# Replace this line:
emergency = scenario_emergency_procurement[s].get(supplier, 0.0)

# With this:
emergency = sum(pyo.value(self.model.flow_emergency[s, arc]) 
                for arc in self.model.EMERGENCY_ARCS 
                if arc[0] == supplier)
```

### Option 3: Remove if Not Needed

If emergency procurement tracking is not essential for your use case, you can:

```python
# Replace the problematic line with:
emergency = 0.0  # Placeholder if emergency procurement not tracked
```

## Full Context Fix Example

Here's a complete example of how the section might look:

```python
def _extract_results(self, status, solve_time):
    """Extract optimization results."""
    results = {
        'status': status,
        'solve_time': solve_time,
        'objective': pyo.value(self.model.objective),
        'scenarios': {}
    }
    
    # Extract emergency procurement for each scenario
    scenario_emergency_procurement = {}
    for s in self.model.SCENARIOS:
        scenario_emergency_procurement[s] = {}
        for supplier in self.model.SUPPLIERS:
            emergency_total = 0
            if hasattr(self.model, 'flow_emergency'):
                for arc in self.model.EMERGENCY_ARCS:
                    if arc[0] == supplier:
                        emergency_total += pyo.value(self.model.flow_emergency[s, arc])
            scenario_emergency_procurement[s][supplier] = emergency_total
    
    # Now you can use scenario_emergency_procurement
    for s in self.model.SCENARIOS:
        for supplier in self.model.SUPPLIERS:
            emergency = scenario_emergency_procurement[s].get(supplier, 0.0)
            # ... rest of your code
```

## Prevention

To prevent similar issues:

1. **Initialize all data structures** before using them
2. **Check variable existence** with `hasattr()` before accessing
3. **Use meaningful variable names** that indicate scope
4. **Add comments** explaining what each data structure contains
5. **Test with try-except** blocks during development:

```python
try:
    emergency = scenario_emergency_procurement[s].get(supplier, 0.0)
except NameError:
    print("Warning: scenario_emergency_procurement not defined, using 0")
    emergency = 0.0
```

## Verification

After applying the fix:

1. Run your optimization again:
   ```bash
   python main.py
   ```

2. Check that the model solves without errors

3. Verify the results are reasonable

## Alternative: Use Repository Version

If you're experiencing multiple issues, consider using the version in this repository which has been tested and validated:

1. Download/clone this repository
2. Use the `model.py` and `solver.py` from here
3. Run with `python main.py --mode demo`

The repository version uses a simpler, cleaner extraction approach that avoids this issue.

## Additional Notes

- The error suggests emergency procurement is being tracked but the data structure wasn't initialized
- Make sure all data extraction happens AFTER the model has been solved
- Consider adding validation to ensure all required variables exist before extraction
- Use the debugger to inspect what variables are available in the scope

## Need More Help?

If this fix doesn't resolve your issue:

1. Check if there are other undefined variables in the same function
2. Verify the model has `flow_emergency` variables defined
3. Ensure the model solved successfully before extracting results
4. Look for other references to `scenario_emergency_procurement` in your code
5. Consider refactoring to match the cleaner approach in this repository's code
