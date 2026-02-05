# Working Reference Implementation for Result Extraction

This file provides a complete, working implementation of result extraction that avoids the `scenario_emergency_procurement` NameError.

## The Problem

Your code has:
```python
# ❌ BROKEN - Line 878 in optimization_model.py
emergency = scenario_emergency_procurement[s].get(supplier, 0.0)
# NameError: 'scenario_emergency_procurement' is not defined
```

## The Solution: Working Code Pattern

Here's the correct way to extract results without pre-defining dictionaries:

### Option 1: Inline Calculation (Simplest - Repository Pattern)

```python
def _extract_results(self, status, solve_time):
    """Extract optimization results - WORKING VERSION."""
    
    results = {
        'status': status,
        'solve_time': solve_time,
        'objective': pyo.value(self.model.objective),
        'first_stage': {},
        'second_stage': {},
        'scenarios': {}
    }
    
    # Extract scenario-specific data
    for s in self.model.SCENARIOS:
        scenario_data = {
            'flows': {},
            'shortages': {},
            'inventory': {},
            'costs': {}
        }
        
        # Calculate emergency procurement INLINE (no pre-definition needed)
        scenario_data['emergency_procurement'] = {}
        for supplier in self.model.SUPPLIERS:
            # Sum emergency flows from this supplier - calculated on the fly
            emergency_total = sum(
                pyo.value(self.model.flow_emergency[s, arc])
                for arc in self.model.EMERGENCY_ARCS
                if arc[0] == supplier  # arc[0] is the source node
            )
            scenario_data['emergency_procurement'][supplier] = emergency_total
        
        # Now you can use it:
        for supplier in self.model.SUPPLIERS:
            emergency = scenario_data['emergency_procurement'].get(supplier, 0.0)
            # Use emergency value here
        
        results['scenarios'][s] = scenario_data
    
    return results
```

### Option 2: Pre-Initialize Dictionary (If You Must Use Variable Name)

```python
def _extract_results(self, status, solve_time):
    """Extract optimization results - WORKING VERSION with pre-initialization."""
    
    results = {
        'status': status,
        'solve_time': solve_time,
        'objective': pyo.value(self.model.objective),
    }
    
    # ============================================================
    # CRITICAL: Initialize BEFORE using
    # ============================================================
    scenario_emergency_procurement = {}
    
    # Populate the dictionary
    for s in self.model.SCENARIOS:
        scenario_emergency_procurement[s] = {}
        
        for supplier in self.model.SUPPLIERS:
            # Calculate emergency procurement for this supplier in this scenario
            emergency_total = 0.0
            
            # Check if emergency flow variables exist
            if hasattr(self.model, 'flow_emergency') and hasattr(self.model, 'EMERGENCY_ARCS'):
                for arc in self.model.EMERGENCY_ARCS:
                    if arc[0] == supplier:  # If supplier is the source
                        try:
                            flow_val = pyo.value(self.model.flow_emergency[s, arc])
                            emergency_total += flow_val if flow_val is not None else 0.0
                        except (KeyError, AttributeError, ValueError):
                            # Handle cases where value doesn't exist
                            pass
            
            scenario_emergency_procurement[s][supplier] = emergency_total
    
    # ============================================================
    # NOW you can use it (after line 878)
    # ============================================================
    for s in self.model.SCENARIOS:
        for supplier in self.model.SUPPLIERS:
            # This now works because scenario_emergency_procurement is defined
            emergency = scenario_emergency_procurement[s].get(supplier, 0.0)
            # ... rest of your code
    
    return results
```

### Option 3: Defensive with Error Handling

```python
def _extract_results(self, status, solve_time):
    """Extract optimization results - WORKING VERSION with maximum safety."""
    
    results = {
        'status': status,
        'solve_time': solve_time,
        'objective': pyo.value(self.model.objective),
    }
    
    # Initialize with defaults to prevent NameError
    scenario_emergency_procurement = {}
    
    try:
        # Safely populate emergency procurement data
        for s in self.model.SCENARIOS:
            scenario_emergency_procurement[s] = {}
            
            for supplier in self.model.SUPPLIERS:
                emergency_total = 0.0
                
                # Safe access with multiple checks
                if (hasattr(self.model, 'flow_emergency') and 
                    hasattr(self.model, 'EMERGENCY_ARCS') and
                    len(self.model.EMERGENCY_ARCS) > 0):
                    
                    for arc in self.model.EMERGENCY_ARCS:
                        if len(arc) >= 2 and arc[0] == supplier:
                            try:
                                val = pyo.value(self.model.flow_emergency[s, arc])
                                if val is not None and not (val != val):  # Check for NaN
                                    emergency_total += float(val)
                            except Exception as e:
                                print(f"Warning: Could not extract flow for {arc}: {e}")
                                continue
                
                scenario_emergency_procurement[s][supplier] = emergency_total
    
    except Exception as e:
        print(f"Warning: Error initializing emergency procurement: {e}")
        # Set all to zero as fallback
        for s in self.model.SCENARIOS:
            scenario_emergency_procurement[s] = {
                supplier: 0.0 for supplier in self.model.SUPPLIERS
            }
    
    # Now safe to use
    for s in self.model.SCENARIOS:
        for supplier in self.model.SUPPLIERS:
            emergency = scenario_emergency_procurement[s].get(supplier, 0.0)
            # ... use emergency
    
    return results
```

## Complete Working Example (Copy This Entire Method)

Here's a complete `_extract_results` method you can copy directly:

```python
import pyomo.environ as pyo

def _extract_results(self, status, solve_time):
    """
    Extract optimization results from solved model.
    
    This version correctly initializes all data structures before use.
    """
    # Initialize result structure
    results = {
        'status': status,
        'solve_time': solve_time,
        'objective': pyo.value(self.model.objective) if status == 'Optimal' else None,
        'first_stage': {
            'hardening': {},
            'prepositioning': {}
        },
        'second_stage': {
            'flows': {},
            'emergency': {},
            'shortages': {},
            'inventory': {}
        },
        'scenarios': {}
    }
    
    # Only extract detailed results if optimal
    if status != 'Optimal':
        return results
    
    # Extract first-stage decisions
    try:
        for arc in self.model.HARDENABLE_ARCS:
            harden_val = pyo.value(self.model.harden[arc])
            if harden_val > 0.5:  # Binary threshold
                results['first_stage']['hardening'][arc] = 1
        
        for dc in self.model.DCS:
            prepos_val = pyo.value(self.model.preposition[dc])
            if prepos_val > 0.01:  # Small threshold for numerical precision
                results['first_stage']['prepositioning'][dc] = prepos_val
    except Exception as e:
        print(f"Warning: Error extracting first-stage: {e}")
    
    # Extract second-stage results for each scenario
    for s in self.model.SCENARIOS:
        scenario_data = {
            'cost': 0.0,
            'flows': {},
            'emergency_procurement': {},
            'shortages': {},
            'inventory': {}
        }
        
        try:
            # Extract flows
            for arc in self.model.SUPPLIER_DC_ARCS:
                flow_val = pyo.value(self.model.flow_supplier_dc[s, arc])
                if flow_val > 0.01:
                    scenario_data['flows'][f'supplier_dc_{arc}'] = flow_val
                    scenario_data['cost'] += pyo.value(self.model.transport_cost[arc]) * flow_val
            
            for arc in self.model.DC_ZONE_ARCS:
                flow_val = pyo.value(self.model.flow_dc_zone[s, arc])
                if flow_val > 0.01:
                    scenario_data['flows'][f'dc_zone_{arc}'] = flow_val
                    scenario_data['cost'] += pyo.value(self.model.transport_cost[arc]) * flow_val
            
            # Extract emergency procurement (INLINE - no pre-definition needed)
            for supplier in self.model.SUPPLIERS:
                emergency_total = 0.0
                for arc in self.model.EMERGENCY_ARCS:
                    if arc[0] == supplier:
                        flow_val = pyo.value(self.model.flow_emergency[s, arc])
                        emergency_total += flow_val
                        scenario_data['cost'] += pyo.value(self.model.transport_cost[arc]) * flow_val
                
                scenario_data['emergency_procurement'][supplier] = emergency_total
            
            # Extract shortages
            for zone in self.model.ZONES:
                shortage_val = pyo.value(self.model.shortage[s, zone])
                if shortage_val > 0.01:
                    scenario_data['shortages'][zone] = shortage_val
                    scenario_data['cost'] += pyo.value(self.model.shortage_penalty) * shortage_val
            
            # Extract inventory
            for dc in self.model.DCS:
                inv_val = pyo.value(self.model.inventory[s, dc])
                if inv_val > 0.01:
                    scenario_data['inventory'][dc] = inv_val
                    scenario_data['cost'] += pyo.value(self.model.holding_cost[dc]) * inv_val
        
        except Exception as e:
            print(f"Warning: Error extracting scenario {s} data: {e}")
            scenario_data['error'] = str(e)
        
        results['scenarios'][s] = scenario_data
    
    return results
```

## Key Principles

1. **Initialize before use**: Always create dictionaries/variables before referencing them
2. **Use inline calculations**: Calculate values when needed rather than pre-storing
3. **Add error handling**: Use try-except to handle missing attributes
4. **Check existence**: Use `hasattr()` before accessing attributes
5. **Provide defaults**: Use `.get(key, default)` for safe dictionary access

## How to Apply This Fix

### For Your Code (Line 878 Fix):

1. **Find line 878** in your `optimization_model.py`
2. **Look backward** to find where the method starts
3. **Add initialization** before line 878:

```python
# Add this BEFORE line 878
scenario_emergency_procurement = {}
for s in self.model.SCENARIOS:
    scenario_emergency_procurement[s] = {}
    for supplier in self.model.SUPPLIERS:
        total = sum(pyo.value(self.model.flow_emergency[s, arc])
                   for arc in self.model.EMERGENCY_ARCS if arc[0] == supplier)
        scenario_emergency_procurement[s][supplier] = total
```

4. **Save and test** your code

## Testing the Fix

After applying the fix, run:
```python
python main.py
```

You should see:
- ✅ No NameError
- ✅ Model solves successfully  
- ✅ Results extracted completely

## Comparison: Wrong vs Right

### ❌ WRONG (Causes NameError):
```python
def _extract_results(self):
    for s in scenarios:
        # Using variable without defining it first
        emergency = scenario_emergency_procurement[s].get(supplier, 0.0)  # ERROR!
```

### ✅ RIGHT (Works):
```python
def _extract_results(self):
    # Option A: Initialize first
    scenario_emergency_procurement = {}
    for s in scenarios:
        scenario_emergency_procurement[s] = calculate_emergency(s)
    
    # NOW use it
    for s in scenarios:
        emergency = scenario_emergency_procurement[s].get(supplier, 0.0)  # OK!

    # Option B: Calculate inline (even better)
    for s in scenarios:
        emergency = calculate_emergency(s, supplier)  # OK!
```

## Need Help?

- See [FIX_YOUR_LOCAL_CODE.md](FIX_YOUR_LOCAL_CODE.md) for step-by-step instructions
- See [BUGFIX_EMERGENCY_PROCUREMENT.md](BUGFIX_EMERGENCY_PROCUREMENT.md) for detailed explanation
- See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for best practices

---

**This is a working reference implementation.** Copy the pattern that fits your needs and apply it to your `optimization_model.py` file.
