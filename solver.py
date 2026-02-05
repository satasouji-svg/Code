"""
Solver interface module for the optimization model.
Interfaces with HiGHS solver via Pyomo.
"""

import pyomo.environ as pyo
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition
from typing import Dict, Any, Optional
import time


class OptimizationSolver:
    """Solver interface for the stochastic programming model."""
    
    def __init__(self, solver_name: str = 'appsi_highs', solver_options: Optional[Dict] = None):
        """
        Initialize the solver.
        
        Args:
            solver_name: Name of the solver ('appsi_highs' or 'highs')
            solver_options: Dictionary of solver-specific options
        """
        self.solver_name = solver_name
        self.solver_options = solver_options or {}
        self.solver = None
        self.results = None
        self.solve_time = None
    
    def solve(self, model: pyo.ConcreteModel, tee: bool = False) -> Dict[str, Any]:
        """
        Solve the optimization model.
        
        Args:
            model: Pyomo ConcreteModel to solve
            tee: Whether to display solver output
            
        Returns:
            Dictionary with solution information
        """
        # Try appsi_highs first (faster interface), fallback to highs
        try:
            self.solver = SolverFactory(self.solver_name)
        except Exception:
            print(f"Solver {self.solver_name} not available, trying 'highs'...")
            self.solver_name = 'highs'
            self.solver = SolverFactory('highs')
        
        # Set solver options
        for key, value in self.solver_options.items():
            self.solver.options[key] = value
        
        # Solve the model
        start_time = time.time()
        try:
            self.results = self.solver.solve(model, tee=tee)
            self.solve_time = time.time() - start_time
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'solve_time': time.time() - start_time
            }
        
        # Extract solution information
        solution_info = self._extract_solution_info(model)
        
        return solution_info
    
    def _extract_solution_info(self, model: pyo.ConcreteModel) -> Dict[str, Any]:
        """Extract solution information from solved model."""
        solution = {
            'solve_time': self.solve_time,
            'solver': self.solver_name
        }
        
        # Check solver status
        if (self.results.solver.status == SolverStatus.ok and
            self.results.solver.termination_condition == TerminationCondition.optimal):
            solution['status'] = 'optimal'
            solution['objective_value'] = pyo.value(model.objective)
            
            # Extract first-stage decisions
            solution['first_stage'] = self._extract_first_stage(model)
            
            # Extract second-stage summary statistics
            solution['second_stage_summary'] = self._extract_second_stage_summary(model)
            
            # Extract CVaR information
            solution['risk_metrics'] = self._extract_risk_metrics(model)
            
        elif self.results.solver.termination_condition == TerminationCondition.infeasible:
            solution['status'] = 'infeasible'
            solution['message'] = 'Model is infeasible'
        else:
            solution['status'] = 'unknown'
            solution['message'] = f'Solver status: {self.results.solver.status}, ' \
                                f'Termination: {self.results.solver.termination_condition}'
        
        return solution
    
    def _extract_first_stage(self, model: pyo.ConcreteModel) -> Dict:
        """Extract first-stage decision variables."""
        first_stage = {
            'hardening': {},
            'prepositioning': {}
        }
        
        # Extract hardening decisions
        for arc in model.HARDENABLE_ARCS:
            value = pyo.value(model.harden[arc])
            if value > 0.5:  # Binary variable threshold
                first_stage['hardening'][arc] = 1
        
        # Extract prepositioning decisions
        for dc in model.DCS:
            value = pyo.value(model.preposition[dc])
            if value > 0.01:  # Small threshold for numerical precision
                first_stage['prepositioning'][dc] = value
        
        return first_stage
    
    def _extract_second_stage_summary(self, model: pyo.ConcreteModel) -> Dict:
        """Extract summary statistics from second-stage decisions."""
        summary = {
            'scenario_costs': {},
            'average_shortage': {},
            'service_levels': {}
        }
        
        # Calculate cost for each scenario
        for s in model.SCENARIOS:
            cost = 0
            # Transport costs
            for arc in model.SUPPLIER_DC_ARCS:
                cost += pyo.value(model.transport_cost[arc] * model.flow_supplier_dc[s, arc])
            for arc in model.DC_ZONE_ARCS:
                cost += pyo.value(model.transport_cost[arc] * model.flow_dc_zone[s, arc])
            for arc in model.EMERGENCY_ARCS:
                cost += pyo.value(model.transport_cost[arc] * model.flow_emergency[s, arc])
            
            # Holding costs
            for dc in model.DCS:
                cost += pyo.value(model.holding_cost[dc] * model.inventory[s, dc])
            
            # Shortage penalties
            for zone in model.ZONES:
                cost += pyo.value(model.shortage_penalty * model.shortage[s, zone])
            
            summary['scenario_costs'][s] = cost
        
        # Calculate average shortage per zone
        for zone in model.ZONES:
            total_shortage = sum(pyo.value(model.shortage[s, zone]) 
                               for s in model.SCENARIOS)
            avg_shortage = total_shortage / len(model.SCENARIOS)
            summary['average_shortage'][zone] = avg_shortage
        
        # Calculate service levels
        for zone in model.ZONES:
            served = 0
            total_demand = 0
            for s in model.SCENARIOS:
                demand = pyo.value(model.demand[s, zone])
                shortage = pyo.value(model.shortage[s, zone])
                served += (demand - shortage)
                total_demand += demand
            
            service_level = served / total_demand if total_demand > 0 else 0
            summary['service_levels'][zone] = service_level
        
        return summary
    
    def _extract_risk_metrics(self, model: pyo.ConcreteModel) -> Dict:
        """Extract risk metrics including CVaR."""
        metrics = {
            'var': pyo.value(model.var) if hasattr(model, 'var') else None,
            'cvar': None,
            'expected_cost': 0
        }
        
        # Calculate CVaR if applicable
        if hasattr(model, 'var') and hasattr(model, 'cvar_excess'):
            alpha = 0.95  # Default, should match model params
            cvar_component = sum(pyo.value(model.scenario_prob[s] * model.cvar_excess[s])
                               for s in model.SCENARIOS)
            metrics['cvar'] = pyo.value(model.var) + cvar_component / (1 - alpha)
        
        # Expected second-stage cost
        if hasattr(model, 'scenario_prob'):
            for s in model.SCENARIOS:
                prob = pyo.value(model.scenario_prob[s])
                # Scenario cost
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
                
                metrics['expected_cost'] += prob * cost
        
        return metrics
    
    def validate_solution(self, model: pyo.ConcreteModel) -> Dict[str, Any]:
        """
        Validate the solution for constraint satisfaction.
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            'valid': True,
            'violations': [],
            'warnings': []
        }
        
        tolerance = 1e-6
        
        # Check probability sum
        if hasattr(model, 'scenario_prob'):
            prob_sum = sum(pyo.value(model.scenario_prob[s]) for s in model.SCENARIOS)
            if abs(prob_sum - 1.0) > tolerance:
                validation['violations'].append(
                    f"Scenario probabilities sum to {prob_sum}, not 1.0"
                )
                validation['valid'] = False
        
        # Check flow conservation at DCs
        for s in model.SCENARIOS:
            for dc in model.DCS:
                inflow = sum(pyo.value(model.flow_supplier_dc[s, arc])
                           for arc in model.SUPPLIER_DC_ARCS if arc[1] == dc)
                inflow += pyo.value(model.preposition[dc])
                
                outflow = sum(pyo.value(model.flow_dc_zone[s, arc])
                            for arc in model.DC_ZONE_ARCS if arc[0] == dc)
                outflow += pyo.value(model.inventory[s, dc])
                
                if abs(inflow - outflow) > tolerance:
                    validation['warnings'].append(
                        f"Flow imbalance at {dc} in scenario {s}: "
                        f"inflow={inflow:.2f}, outflow={outflow:.2f}"
                    )
        
        # Check non-negativity
        for s in model.SCENARIOS:
            for arc in model.SUPPLIER_DC_ARCS:
                if pyo.value(model.flow_supplier_dc[s, arc]) < -tolerance:
                    validation['violations'].append(
                        f"Negative flow on {arc} in scenario {s}"
                    )
                    validation['valid'] = False
        
        return validation


def solve_with_time_limit(model: pyo.ConcreteModel, 
                          time_limit: int = 300,
                          gap: float = 0.01) -> Dict[str, Any]:
    """
    Solve model with time limit and optimality gap.
    
    Args:
        model: Pyomo model to solve
        time_limit: Time limit in seconds
        gap: Relative optimality gap (e.g., 0.01 = 1%)
        
    Returns:
        Solution dictionary
    """
    solver_options = {
        'time_limit': time_limit,
        'mip_rel_gap': gap
    }
    
    solver = OptimizationSolver(solver_options=solver_options)
    solution = solver.solve(model, tee=True)
    
    return solution
