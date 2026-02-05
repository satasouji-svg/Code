"""
Validation module for model correctness and solution feasibility.
Validates flow conservation, probability sums, bounds, and operational constraints.
"""

import pyomo.environ as pyo
import numpy as np
from typing import Dict, List, Any, Tuple
from config import NetworkConfig, ModelParameters
from scenario_gen import Scenario


class ModelValidator:
    """Validate optimization model and solutions."""
    
    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
        self.validation_results = {}
    
    def validate_model_structure(self, model: pyo.ConcreteModel) -> Dict[str, Any]:
        """Validate the structure of the optimization model."""
        results = {
            'valid': True,
            'checks': [],
            'errors': [],
            'warnings': []
        }
        
        # Check sets are defined
        required_sets = ['SUPPLIERS', 'DCS', 'ZONES', 'SCENARIOS',
                        'SUPPLIER_DC_ARCS', 'DC_ZONE_ARCS', 'EMERGENCY_ARCS']
        for set_name in required_sets:
            if hasattr(model, set_name):
                results['checks'].append(f"✓ Set {set_name} defined")
            else:
                results['errors'].append(f"✗ Set {set_name} missing")
                results['valid'] = False
        
        # Check variables are defined
        required_vars = ['harden', 'preposition', 'flow_supplier_dc',
                        'flow_dc_zone', 'shortage', 'var', 'cvar_excess']
        for var_name in required_vars:
            if hasattr(model, var_name):
                results['checks'].append(f"✓ Variable {var_name} defined")
            else:
                results['errors'].append(f"✗ Variable {var_name} missing")
                results['valid'] = False
        
        # Check constraints are defined
        required_constraints = ['hardening_budget_constraint', 'supplier_capacity_constraint',
                               'dc_balance', 'demand_satisfaction', 'cvar_excess_constraint']
        for cons_name in required_constraints:
            if hasattr(model, cons_name):
                results['checks'].append(f"✓ Constraint {cons_name} defined")
            else:
                results['errors'].append(f"✗ Constraint {cons_name} missing")
                results['valid'] = False
        
        # Check objective is defined
        if hasattr(model, 'objective'):
            results['checks'].append("✓ Objective function defined")
        else:
            results['errors'].append("✗ Objective function missing")
            results['valid'] = False
        
        return results
    
    def validate_scenario_probabilities(self, scenarios: List[Scenario]) -> Dict[str, Any]:
        """Validate that scenario probabilities sum to 1."""
        results = {
            'valid': True,
            'checks': [],
            'errors': []
        }
        
        prob_sum = sum(s.probability for s in scenarios)
        
        if abs(prob_sum - 1.0) < self.tolerance:
            results['checks'].append(f"✓ Probabilities sum to {prob_sum:.6f}")
        else:
            results['errors'].append(
                f"✗ Probabilities sum to {prob_sum:.6f}, expected 1.0"
            )
            results['valid'] = False
        
        # Check all probabilities are non-negative
        for s in scenarios:
            if s.probability < 0:
                results['errors'].append(
                    f"✗ Scenario {s.id} has negative probability {s.probability}"
                )
                results['valid'] = False
        
        if all(s.probability >= 0 for s in scenarios):
            results['checks'].append("✓ All probabilities are non-negative")
        
        return results
    
    def validate_solution_feasibility(self, model: pyo.ConcreteModel) -> Dict[str, Any]:
        """Validate that the solution satisfies all constraints."""
        results = {
            'valid': True,
            'checks': [],
            'errors': [],
            'warnings': []
        }
        
        # Check flow conservation at DCs
        flow_violations = self._check_flow_conservation(model)
        if not flow_violations:
            results['checks'].append("✓ Flow conservation satisfied at all DCs")
        else:
            results['errors'].extend(flow_violations)
            results['valid'] = False
        
        # Check demand satisfaction
        demand_violations = self._check_demand_satisfaction(model)
        if not demand_violations:
            results['checks'].append("✓ Demand constraints satisfied")
        else:
            results['errors'].extend(demand_violations)
            results['valid'] = False
        
        # Check capacity constraints
        capacity_violations = self._check_capacity_constraints(model)
        if not capacity_violations:
            results['checks'].append("✓ Capacity constraints satisfied")
        else:
            results['warnings'].extend(capacity_violations)
        
        # Check non-negativity
        negativity_violations = self._check_non_negativity(model)
        if not negativity_violations:
            results['checks'].append("✓ Non-negativity constraints satisfied")
        else:
            results['errors'].extend(negativity_violations)
            results['valid'] = False
        
        # Check hardening budget
        if hasattr(model, 'hardening_budget_constraint'):
            budget_used = sum(pyo.value(model.hardening_cost[arc] * model.harden[arc])
                            for arc in model.HARDENABLE_ARCS)
            budget_limit = pyo.value(model.hardening_budget_constraint.upper)
            
            if budget_used <= budget_limit + self.tolerance:
                results['checks'].append(
                    f"✓ Hardening budget satisfied: ${budget_used:.2f} <= ${budget_limit:.2f}"
                )
            else:
                results['errors'].append(
                    f"✗ Hardening budget violated: ${budget_used:.2f} > ${budget_limit:.2f}"
                )
                results['valid'] = False
        
        return results
    
    def _check_flow_conservation(self, model: pyo.ConcreteModel) -> List[str]:
        """Check flow conservation at distribution centers."""
        violations = []
        
        for s in model.SCENARIOS:
            for dc in model.DCS:
                # Inflow
                inflow = sum(pyo.value(model.flow_supplier_dc[s, arc])
                           for arc in model.SUPPLIER_DC_ARCS if arc[1] == dc)
                inflow += pyo.value(model.preposition[dc])
                
                # Outflow
                outflow = sum(pyo.value(model.flow_dc_zone[s, arc])
                            for arc in model.DC_ZONE_ARCS if arc[0] == dc)
                outflow += pyo.value(model.inventory[s, dc])
                
                if abs(inflow - outflow) > self.tolerance:
                    violations.append(
                        f"✗ Flow imbalance at {dc} in scenario {s}: "
                        f"inflow={inflow:.4f}, outflow={outflow:.4f}"
                    )
        
        return violations
    
    def _check_demand_satisfaction(self, model: pyo.ConcreteModel) -> List[str]:
        """Check that demand is satisfied (including shortage)."""
        violations = []
        
        for s in model.SCENARIOS:
            for zone in model.ZONES:
                # Supply to zone
                supply = sum(pyo.value(model.flow_dc_zone[s, arc])
                           for arc in model.DC_ZONE_ARCS if arc[1] == zone)
                supply += sum(pyo.value(model.flow_emergency[s, arc])
                            for arc in model.EMERGENCY_ARCS if arc[1] == zone)
                supply += pyo.value(model.shortage[s, zone])
                
                demand = pyo.value(model.demand[s, zone])
                
                if supply < demand - self.tolerance:
                    violations.append(
                        f"✗ Demand not satisfied at {zone} in scenario {s}: "
                        f"supply={supply:.4f}, demand={demand:.4f}"
                    )
        
        return violations
    
    def _check_capacity_constraints(self, model: pyo.ConcreteModel) -> List[str]:
        """Check capacity constraints."""
        violations = []
        
        # Supplier capacities
        for s in model.SCENARIOS:
            for supplier in model.SUPPLIERS:
                outflow = sum(pyo.value(model.flow_supplier_dc[s, arc])
                            for arc in model.SUPPLIER_DC_ARCS if arc[0] == supplier)
                outflow += sum(pyo.value(model.flow_emergency[s, arc])
                             for arc in model.EMERGENCY_ARCS if arc[0] == supplier)
                
                capacity = pyo.value(model.supplier_capacity[supplier])
                
                if outflow > capacity + self.tolerance:
                    violations.append(
                        f"⚠ Supplier capacity exceeded at {supplier} in scenario {s}: "
                        f"outflow={outflow:.4f}, capacity={capacity:.4f}"
                    )
        
        # DC storage capacities
        for s in model.SCENARIOS:
            for dc in model.DCS:
                inventory = pyo.value(model.inventory[s, dc])
                capacity = pyo.value(model.dc_storage[dc])
                
                if inventory > capacity + self.tolerance:
                    violations.append(
                        f"⚠ Storage capacity exceeded at {dc} in scenario {s}: "
                        f"inventory={inventory:.4f}, capacity={capacity:.4f}"
                    )
        
        return violations
    
    def _check_non_negativity(self, model: pyo.ConcreteModel) -> List[str]:
        """Check non-negativity of decision variables."""
        violations = []
        
        # Check flows
        for s in model.SCENARIOS:
            for arc in model.SUPPLIER_DC_ARCS:
                if pyo.value(model.flow_supplier_dc[s, arc]) < -self.tolerance:
                    violations.append(
                        f"✗ Negative flow on supplier-DC arc {arc} in scenario {s}"
                    )
            
            for arc in model.DC_ZONE_ARCS:
                if pyo.value(model.flow_dc_zone[s, arc]) < -self.tolerance:
                    violations.append(
                        f"✗ Negative flow on DC-zone arc {arc} in scenario {s}"
                    )
            
            for zone in model.ZONES:
                if pyo.value(model.shortage[s, zone]) < -self.tolerance:
                    violations.append(
                        f"✗ Negative shortage at {zone} in scenario {s}"
                    )
        
        return violations
    
    def validate_cvar_calculation(self, model: pyo.ConcreteModel,
                                  alpha: float) -> Dict[str, Any]:
        """Validate CVaR calculation."""
        results = {
            'valid': True,
            'checks': [],
            'errors': []
        }
        
        if not hasattr(model, 'var') or not hasattr(model, 'cvar_excess'):
            results['errors'].append("✗ CVaR variables not found in model")
            results['valid'] = False
            return results
        
        var_value = pyo.value(model.var)
        
        # Calculate scenario costs and check CVaR excess
        for s in model.SCENARIOS:
            # Calculate scenario cost
            cost = 0
            for arc in model.SUPPLIER_DC_ARCS:
                cost += pyo.value(model.transport_cost[arc] * model.flow_supplier_dc[s, arc])
            for arc in model.DC_ZONE_ARCS:
                cost += pyo.value(model.transport_cost[arc] * model.flow_dc_zone[s, arc])
            for arc in model.EMERGENCY_ARCS:
                cost += pyo.value(model.transport_cost[arc] * model.flow_emergency[s, arc])
            for dc in model.DCS:
                cost += pyo.value(model.holding_cost[dc] * model.inventory[s, dc])
            for zone in model.ZONES:
                cost += pyo.value(model.shortage_penalty * model.shortage[s, zone])
            
            excess = pyo.value(model.cvar_excess[s])
            expected_excess = max(0, cost - var_value)
            
            if abs(excess - expected_excess) > self.tolerance:
                results['warnings'] = results.get('warnings', [])
                results['warnings'].append(
                    f"⚠ CVaR excess mismatch in scenario {s}: "
                    f"excess={excess:.4f}, expected={expected_excess:.4f}"
                )
        
        results['checks'].append("✓ CVaR calculation structure validated")
        
        return results
    
    def print_validation_report(self, validation_results: Dict[str, Any]):
        """Print formatted validation report."""
        print("\n" + "="*60)
        print("VALIDATION REPORT")
        print("="*60)
        
        print(f"\nOverall Status: {'VALID' if validation_results['valid'] else 'INVALID'}")
        
        if validation_results.get('checks'):
            print("\nPassed Checks:")
            for check in validation_results['checks']:
                print(f"  {check}")
        
        if validation_results.get('warnings'):
            print("\nWarnings:")
            for warning in validation_results['warnings']:
                print(f"  {warning}")
        
        if validation_results.get('errors'):
            print("\nErrors:")
            for error in validation_results['errors']:
                print(f"  {error}")
        
        print("="*60 + "\n")
