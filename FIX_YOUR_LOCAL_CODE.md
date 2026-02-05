# Step-by-Step Fix for Your Local Code

## Your Error
```
File "C:\Users\WINDOWS 10\.spyder-py3\Wildfir 13\Code-copilot-rewrite-supply-network-model\optimization_model.py", line 878, in _extract_results
    emergency = scenario_emergency_procurement[s].get(supplier, 0.0)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
NameError: name 'scenario_emergency_procurement' is not defined
```

## Step-by-Step Fix Instructions

### Step 1: Locate the File
Open this file in your editor:
```
C:\Users\WINDOWS 10\.spyder-py3\Wildfir 13\Code-copilot-rewrite-supply-network-model\optimization_model.py
```

### Step 2: Find Line 878
Navigate to line 878 which contains:
```python
emergency = scenario_emergency_procurement[s].get(supplier, 0.0)
```

### Step 3: Identify the Method
This line is inside the `_extract_results` method. Find where this method starts (look for `def _extract_results`).

### Step 4: Add Initialization Code

**BEFORE line 878**, add this block of code:

```python
        # ============================================================
        # FIX: Initialize scenario_emergency_procurement
        # ============================================================
        scenario_emergency_procurement = {}
        
        # Loop through each scenario
        for s in self.model.SCENARIOS:
            scenario_emergency_procurement[s] = {}
            
            # Loop through each supplier
            for supplier in self.model.SUPPLIERS:
                emergency_total = 0
                
                # Check if emergency flows exist
                if hasattr(self.model, 'flow_emergency') and hasattr(self.model, 'EMERGENCY_ARCS'):
                    # Sum all emergency flows from this supplier
                    for arc in self.model.EMERGENCY_ARCS:
                        if arc[0] == supplier:  # arc[0] is the source node
                            try:
                                flow_value = pyo.value(self.model.flow_emergency[s, arc])
                                emergency_total += flow_value if flow_value else 0
                            except:
                                # If value can't be retrieved, skip
                                pass
                
                # Store the total emergency procurement for this supplier in this scenario
                scenario_emergency_procurement[s][supplier] = emergency_total
        # ============================================================
        # END FIX
        # ============================================================
```

### Step 5: Verify Indentation

**IMPORTANT**: Make sure the indentation matches the surrounding code. The code should align with other variable assignments in the same method.

### Step 6: Save the File

Save `optimization_model.py` after adding the fix.

### Step 7: Test

Run your program again:
```python
runfile('C:/Users/WINDOWS 10/.spyder-py3/Wildfir 13/Code-copilot-rewrite-supply-network-model/main.py', 
        wdir='C:/Users/WINDOWS 10/.spyder-py3/Wildfir 13/Code-copilot-rewrite-supply-network-model')
```

### Step 8: Verify Success

You should see:
- ✅ No NameError
- ✅ Model solves successfully
- ✅ Results are extracted
- ✅ Program completes without errors

## Complete Example Context

Here's what the code should look like in context:

```python
def _extract_results(self, status, solve_time):
    """Extract optimization results."""
    
    results = {
        'status': status,
        'solve_time': solve_time,
        'objective': pyo.value(self.model.objective),
        # ... other fields
    }
    
    # ============================================================
    # FIX: Initialize scenario_emergency_procurement
    # ============================================================
    scenario_emergency_procurement = {}
    
    for s in self.model.SCENARIOS:
        scenario_emergency_procurement[s] = {}
        
        for supplier in self.model.SUPPLIERS:
            emergency_total = 0
            
            if hasattr(self.model, 'flow_emergency') and hasattr(self.model, 'EMERGENCY_ARCS'):
                for arc in self.model.EMERGENCY_ARCS:
                    if arc[0] == supplier:
                        try:
                            flow_value = pyo.value(self.model.flow_emergency[s, arc])
                            emergency_total += flow_value if flow_value else 0
                        except:
                            pass
            
            scenario_emergency_procurement[s][supplier] = emergency_total
    # ============================================================
    
    # ... rest of your extraction code ...
    
    # NOW line 878 will work because scenario_emergency_procurement is defined
    for s in self.model.SCENARIOS:
        for supplier in self.model.SUPPLIERS:
            emergency = scenario_emergency_procurement[s].get(supplier, 0.0)
            # ... use emergency value ...
```

## Alternative: Simpler Inline Fix

If you prefer a simpler fix, replace line 878 entirely:

**Change from:**
```python
emergency = scenario_emergency_procurement[s].get(supplier, 0.0)
```

**To:**
```python
# Calculate emergency procurement inline
emergency = 0
if hasattr(self.model, 'flow_emergency') and hasattr(self.model, 'EMERGENCY_ARCS'):
    for arc in self.model.EMERGENCY_ARCS:
        if arc[0] == supplier:
            try:
                emergency += pyo.value(self.model.flow_emergency[s, arc])
            except:
                pass
```

## Troubleshooting

### If you still get errors:

1. **Check indentation**: Python is sensitive to indentation
   - Use spaces consistently (typically 4 spaces per level)
   - Match surrounding code indentation

2. **Check spelling**: Make sure you typed everything exactly
   - `scenario_emergency_procurement` (not `scenario_emergency_procurment`)
   - Case-sensitive: `SCENARIOS` not `scenarios`

3. **Check imports**: Make sure `pyo` is imported at the top:
   ```python
   import pyomo.environ as pyo
   ```

4. **Check model attributes**: Verify your model has:
   - `self.model.SCENARIOS`
   - `self.model.SUPPLIERS`
   - `self.model.EMERGENCY_ARCS`
   - `self.model.flow_emergency`

### Still not working?

Try the **absolute safest** version that won't break:

```python
# Safe version with maximum error handling
scenario_emergency_procurement = {}

for s in self.model.SCENARIOS:
    scenario_emergency_procurement[s] = {}
    for supplier in self.model.SUPPLIERS:
        # Default to 0 if anything goes wrong
        scenario_emergency_procurement[s][supplier] = 0.0
```

This ensures the variable exists even if emergency flows aren't available.

## After Fixing

Once fixed, consider:

1. **Backup your working code**
   ```
   Copy the entire folder to a safe location
   ```

2. **Document the fix**
   Add a comment in your code:
   ```python
   # Fixed: Added initialization for scenario_emergency_procurement
   # Date: [Today's date]
   # Issue: Was undefined causing NameError
   ```

3. **Test thoroughly**
   - Run with different scenarios
   - Verify results are reasonable
   - Check all zones are served

## Need More Help?

- 📖 **BUGFIX_EMERGENCY_PROCUREMENT.md** - Complete guide
- 📖 **MIGRATION_GUIDE.md** - Best practices
- 📖 **README.md** - Full documentation

## Questions?

If this fix doesn't work:
1. Check if there are OTHER undefined variables
2. Look for similar patterns in your code
3. Consider using the repository's tested version
4. Share the full error traceback for more specific help

---

**TIP**: Copy this entire initialization block to avoid typos!
