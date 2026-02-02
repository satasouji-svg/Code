"""
Two-stage stochastic MILP model for wildfire-resilient supply network optimization.

This module implements a mathematically rigorous two-stage stochastic program with:
- First stage: Preparedness decisions (inventory prepositioning)
- Second stage: Recourse decisions (procurement, routing under scenarios)
- CVaR (Conditional Value at Risk) for risk-averse optimization
- Equity constraints for fair demand satisfaction
"""

import pulp
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from config import Config
from scenario_generator import Scenario


@dataclass
class OptimizationResult:
    """Container for optimization results."""
    
    status: str
    objective_value: float
    solve_time: float
    
    # First stage decisions
    prepositioned_inventory: Dict[str, float]
    
    # Second stage decisions (per scenario)
    scenario_costs: Dict[int, float]
    scenario_flows: Dict[int, Dict[Tuple[str, str], float]]
    scenario_unmet_demand: Dict[int, Dict[str, float]]
    scenario_emergency_procurement: Dict[int, Dict[str, float]]
    
    # Risk measures
    expected_cost: float
    cvar_value: float
    var_value: float
    
    # Equity measures
    min_satisfaction_ratio: float
    avg_satisfaction_ratio: float
    
    # Risk measure diagnostics (for auditability) - with defaults
    tail_scenarios: List[int] = None  # Scenario IDs in CVaR tail
    tail_probability: float = 0.0     # Total probability mass in tail
    
    # Capacity utilization metrics - with defaults
    avg_supplier_utilization: Dict[str, float] = None
    avg_dc_utilization: Dict[str, float] = None
    avg_arc_utilization: Dict[Tuple[str, str], float] = None
    scenarios_with_emergency: int = 0
    total_emergency_procurement: float = 0.0
    
    # Binding constraint diagnostics - with defaults
    tight_supplier_constraints: List[Tuple[str, int, float]] = None  # (supplier, scenario, slack)
    tight_dc_constraints: List[Tuple[str, float]] = None              # (dc, slack)
    tight_arc_constraints: List[Tuple[Tuple[str, str], int, float]] = None  # (arc, scenario, slack)
    emergency_capacity_usage: Dict[int, Dict[str, float]] = None      # scenario -> supplier -> usage %


class TwoStageStochasticModel:
    """Two-stage stochastic MILP model builder and solver."""
    
    def __init__(self, config: Config, scenarios: List[Scenario]):
        """
        Initialize the optimization model.
        
        Args:
            config: Configuration object with all parameters
            scenarios: List of scenarios for stochastic optimization
        """
        self.config = config
        self.scenarios = scenarios
        self.model: Optional[pulp.LpProblem] = None
        self.variables = {}
        
    def build_model(self):
        """
        Build the complete two-stage stochastic MILP model.
        
        This creates all variables, constraints, and the objective function
        with proper CVaR formulation and equity considerations.
        """
        print("🔨 Building optimization model...")
        
        # Initialize model
        self.model = pulp.LpProblem("Wildfire_Resilient_Supply_Network", pulp.LpMinimize)
        
        # Build decision variables
        self._create_variables()
        
        # Add constraints
        self._add_first_stage_constraints()
        self._add_second_stage_constraints()
        self._add_cvar_constraints()
        self._add_equity_constraints()
        
        # Set objective function
        self._set_objective()
        
        print("✅ Model built successfully")
        print(f"   Variables: {len(self.model.variables())}")
        print(f"   Constraints: {len(self.model.constraints)}")
    
    def _create_variables(self):
        """Create all decision variables for the model."""
        net = self.config.network
        opt = self.config.optimization
        
        # ===== FIRST STAGE VARIABLES =====
        # Prepositioned inventory at each distribution center
        self.variables['inventory'] = {}
        for dc in net.distribution_centers:
            storage_cap = net.facilities[dc].get('storage_capacity', float('inf'))
            self.variables['inventory'][dc] = pulp.LpVariable(
                f"inventory_{dc}",
                lowBound=0,
                upBound=storage_cap,
                cat='Continuous'
            )
        
        # ===== SECOND STAGE VARIABLES (per scenario) =====
        self.variables['flow'] = {}
        self.variables['unmet_demand'] = {}
        self.variables['emergency_procurement'] = {}
        
        for scenario in self.scenarios:
            s = scenario.id
            
            # Flow on each arc
            self.variables['flow'][s] = {}
            for arc in net.arcs.keys():
                self.variables['flow'][s][arc] = pulp.LpVariable(
                    f"flow_{arc[0]}_{arc[1]}_s{s}",
                    lowBound=0,
                    cat='Continuous'
                )
            
            # Unmet demand at each demand node
            self.variables['unmet_demand'][s] = {}
            for node in net.demand_nodes:
                self.variables['unmet_demand'][s][node] = pulp.LpVariable(
                    f"unmet_demand_{node}_s{s}",
                    lowBound=0,
                    cat='Continuous'
                )
            
            # Emergency procurement at each supplier
            self.variables['emergency_procurement'][s] = {}
            for supplier in net.suppliers:
                self.variables['emergency_procurement'][s][supplier] = pulp.LpVariable(
                    f"emergency_proc_{supplier}_s{s}",
                    lowBound=0,
                    cat='Continuous'
                )
        
        # ===== CVaR VARIABLES =====
        # VaR (Value at Risk) - threshold for CVaR calculation
        self.variables['var'] = pulp.LpVariable(
            "VaR",
            lowBound=None,
            cat='Continuous'
        )
        
        # Excess cost above VaR for each scenario (for CVaR calculation)
        self.variables['excess'] = {}
        for scenario in self.scenarios:
            s = scenario.id
            self.variables['excess'][s] = pulp.LpVariable(
                f"excess_s{s}",
                lowBound=0,
                cat='Continuous'
            )
    
    def _add_first_stage_constraints(self):
        """Add first stage constraints for preparedness decisions."""
        net = self.config.network
        
        # Storage capacity constraints are already enforced by variable bounds
        # No additional first-stage constraints needed in this formulation
        pass
    
    def _add_second_stage_constraints(self):
        """Add second stage constraints for recourse decisions."""
        net = self.config.network
        
        for scenario in self.scenarios:
            s = scenario.id
            
            # === Flow conservation at distribution centers ===
            for dc in net.distribution_centers:
                # Inflow from suppliers
                inflow = pulp.lpSum([
                    self.variables['flow'][s][(source, dc)]
                    for source in net.suppliers
                    if (source, dc) in net.arcs
                ])
                
                # Outflow to demand nodes
                outflow = pulp.lpSum([
                    self.variables['flow'][s][(dc, target)]
                    for target in net.demand_nodes
                    if (dc, target) in net.arcs
                ])
                
                # Add prepositioned inventory
                inventory = self.variables['inventory'][dc]
                
                # Conservation: inflow + inventory = outflow
                self.model += (
                    inflow + inventory == outflow,
                    f"flow_conservation_{dc}_s{s}"
                )
            
            # === Capacity constraints on arcs ===
            for arc, arc_data in net.arcs.items():
                base_capacity = arc_data['capacity']
                capacity_factor = scenario.arc_capacity_factors[arc]
                effective_capacity = base_capacity * capacity_factor
                
                # Only add constraint if effective capacity is non-negligible
                if effective_capacity > self.config.optimization.tolerance:
                    self.model += (
                        self.variables['flow'][s][arc] <= effective_capacity,
                        f"arc_capacity_{arc[0]}_{arc[1]}_s{s}"
                    )
                else:
                    # Force flow to zero for disrupted arcs
                    self.model += (
                        self.variables['flow'][s][arc] == 0,
                        f"arc_disrupted_{arc[0]}_{arc[1]}_s{s}"
                    )
            
            # === Supply constraints at suppliers ===
            for supplier in net.suppliers:
                base_capacity = net.facilities[supplier]['capacity']
                capacity_factor = scenario.facility_capacity_factors[supplier]
                effective_capacity = base_capacity * capacity_factor
                
                # Total outflow from supplier
                total_outflow = pulp.lpSum([
                    self.variables['flow'][s][(supplier, target)]
                    for target in net.distribution_centers
                    if (supplier, target) in net.arcs
                ])
                
                # Add emergency procurement
                emergency = self.variables['emergency_procurement'][s][supplier]
                
                # Capacity constraint
                self.model += (
                    total_outflow <= effective_capacity + emergency,
                    f"supplier_capacity_{supplier}_s{s}"
                )
            
            # === Demand satisfaction constraints ===
            for node in net.demand_nodes:
                demand = scenario.demand[node]
                
                # Total inflow to demand node
                total_inflow = pulp.lpSum([
                    self.variables['flow'][s][(source, node)]
                    for source in net.distribution_centers
                    if (source, node) in net.arcs
                ])
                
                # Demand satisfaction with unmet demand
                unmet = self.variables['unmet_demand'][s][node]
                
                self.model += (
                    total_inflow + unmet == demand,
                    f"demand_satisfaction_{node}_s{s}"
                )
    
    def _add_cvar_constraints(self):
        """
        Add CVaR (Conditional Value at Risk) constraints.
        
        CVaR is calculated using the auxiliary variable approach:
        CVaR_α = VaR_α + (1/(1-α)) * E[max(Cost - VaR_α, 0)]
        """
        alpha = self.config.optimization.cvar_alpha
        
        for scenario in self.scenarios:
            s = scenario.id
            prob = scenario.probability
            
            # Calculate scenario cost
            scenario_cost = self._get_scenario_cost_expression(s)
            
            # Excess cost above VaR
            # excess[s] >= scenario_cost - VaR
            # excess[s] >= 0 (already enforced by variable bounds)
            self.model += (
                self.variables['excess'][s] >= scenario_cost - self.variables['var'],
                f"cvar_excess_s{s}"
            )
    
    def _add_equity_constraints(self):
        """
        Add equity constraints to ensure fair demand satisfaction.
        
        Each demand node must satisfy at least a minimum fraction of its demand
        across scenarios (on average or per scenario).
        """
        net = self.config.network
        min_satisfaction = self.config.optimization.min_demand_satisfaction
        
        # Per-scenario equity constraints
        for scenario in self.scenarios:
            s = scenario.id
            
            for node in net.demand_nodes:
                demand = scenario.demand[node]
                unmet = self.variables['unmet_demand'][s][node]
                
                # Ensure at least min_satisfaction fraction is met
                # (demand - unmet) / demand >= min_satisfaction
                # demand - unmet >= min_satisfaction * demand
                # unmet <= (1 - min_satisfaction) * demand
                self.model += (
                    unmet <= (1 - min_satisfaction) * demand,
                    f"equity_{node}_s{s}"
                )
    
    def _get_scenario_cost_expression(self, scenario_id: int):
        """
        Get the total cost expression for a given scenario.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            PuLP expression for total scenario cost
        """
        net = self.config.network
        opt = self.config.optimization
        
        # Transportation costs
        transport_cost = pulp.lpSum([
            self.variables['flow'][scenario_id][arc] * net.arcs[arc]['cost']
            for arc in net.arcs.keys()
        ])
        
        # Emergency procurement costs
        emergency_cost = pulp.lpSum([
            self.variables['emergency_procurement'][scenario_id][supplier] 
            * opt.emergency_procurement_cost
            for supplier in net.suppliers
        ])
        
        # Unmet demand penalties
        penalty_cost = pulp.lpSum([
            self.variables['unmet_demand'][scenario_id][node] 
            * opt.unmet_demand_penalty
            for node in net.demand_nodes
        ])
        
        return transport_cost + emergency_cost + penalty_cost
    
    def _set_objective(self):
        """
        Set the objective function.
        
        Objective = First-stage costs + CVaR-adjusted second-stage costs
        where CVaR-adjusted cost = w1 * E[Q] + w2 * CVaR_α[Q]
        """
        net = self.config.network
        opt = self.config.optimization
        
        # ===== FIRST STAGE COSTS =====
        # Inventory holding costs
        first_stage_cost = pulp.lpSum([
            self.variables['inventory'][dc] * net.facilities[dc]['holding_cost']
            for dc in net.distribution_centers
        ])
        
        # ===== SECOND STAGE COSTS =====
        # Expected cost E[Q]
        expected_cost = pulp.lpSum([
            scenario.probability * self._get_scenario_cost_expression(scenario.id)
            for scenario in self.scenarios
        ])
        
        # CVaR calculation
        # CVaR_α = VaR + (1/(1-α)) * E[excess]
        alpha = opt.cvar_alpha
        expected_excess = pulp.lpSum([
            scenario.probability * self.variables['excess'][scenario.id]
            for scenario in self.scenarios
        ])
        
        cvar = self.variables['var'] + (1.0 / (1.0 - alpha)) * expected_excess
        
        # ===== COMBINED OBJECTIVE =====
        # Weighted combination of expected cost and CVaR
        w_exp = opt.expectation_weight
        w_cvar = opt.cvar_weight
        
        risk_adjusted_cost = w_exp * expected_cost + w_cvar * cvar
        
        total_objective = first_stage_cost + risk_adjusted_cost
        
        self.model += total_objective
    
    def solve(self) -> OptimizationResult:
        """
        Solve the optimization model.
        
        Returns:
            OptimizationResult object with solution details
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        print("🚀 Solving optimization model...")
        
        # Configure solver
        solver = pulp.PULP_CBC_CMD(
            timeLimit=self.config.optimization.solver_time_limit,
            gapRel=self.config.optimization.solver_gap,
            msg=1
        )
        
        # Solve
        import time
        start_time = time.time()
        status = self.model.solve(solver)
        solve_time = time.time() - start_time
        
        # Extract results
        result = self._extract_results(status, solve_time)
        
        print(f"✅ Optimization completed in {solve_time:.2f}s")
        print(f"   Status: {result.status}")
        print(f"   Objective value: ${result.objective_value:,.2f}")
        
        return result
    
    def _extract_results(self, status: int, solve_time: float) -> OptimizationResult:
        """Extract results from solved model."""
        status_map = {
            pulp.LpStatusOptimal: "Optimal",
            pulp.LpStatusNotSolved: "Not Solved",
            pulp.LpStatusInfeasible: "Infeasible",
            pulp.LpStatusUnbounded: "Unbounded",
            pulp.LpStatusUndefined: "Undefined",
        }
        
        status_str = status_map.get(status, "Unknown")
        
        if status != pulp.LpStatusOptimal:
            # Return empty result for non-optimal solutions
            return OptimizationResult(
                status=status_str,
                objective_value=float('inf'),
                solve_time=solve_time,
                prepositioned_inventory={},
                scenario_costs={},
                scenario_flows={},
                scenario_unmet_demand={},
                scenario_emergency_procurement={},
                expected_cost=float('inf'),
                cvar_value=float('inf'),
                var_value=float('inf'),
                min_satisfaction_ratio=0.0,
                avg_satisfaction_ratio=0.0
            )
        
        # Extract first stage decisions
        prepositioned_inventory = {}
        for dc in self.config.network.distribution_centers:
            prepositioned_inventory[dc] = pulp.value(self.variables['inventory'][dc])
        
        # Extract second stage decisions
        scenario_costs = {}
        scenario_flows = {}
        scenario_unmet_demand = {}
        scenario_emergency_procurement = {}
        
        for scenario in self.scenarios:
            s = scenario.id
            
            # Scenario cost
            scenario_costs[s] = pulp.value(
                self._get_scenario_cost_expression(s)
            )
            
            # Flows
            scenario_flows[s] = {}
            for arc in self.config.network.arcs.keys():
                flow_val = pulp.value(self.variables['flow'][s][arc])
                if flow_val > 1e-6:  # Only store non-zero flows
                    scenario_flows[s][arc] = flow_val
            
            # Unmet demand
            scenario_unmet_demand[s] = {}
            for node in self.config.network.demand_nodes:
                unmet_val = pulp.value(self.variables['unmet_demand'][s][node])
                scenario_unmet_demand[s][node] = unmet_val
            
            # Emergency procurement
            scenario_emergency_procurement[s] = {}
            for supplier in self.config.network.suppliers:
                proc_val = pulp.value(self.variables['emergency_procurement'][s][supplier])
                if proc_val > 1e-6:
                    scenario_emergency_procurement[s][supplier] = proc_val
        
        # Calculate risk measures with proper probability weighting
        expected_cost = sum(
            scenario.probability * scenario_costs[scenario.id]
            for scenario in self.scenarios
        )
        
        # Compute VaR as probability-weighted α-quantile
        # Sort scenarios by cost
        sorted_scenarios = sorted(self.scenarios, key=lambda s: scenario_costs[s.id])
        cumulative_prob = 0.0
        alpha = self.config.optimization.cvar_alpha
        var_scenario_idx = 0
        
        for idx, scenario in enumerate(sorted_scenarios):
            cumulative_prob += scenario.probability
            if cumulative_prob >= alpha:
                var_scenario_idx = idx
                break
        
        var_value = scenario_costs[sorted_scenarios[var_scenario_idx].id]
        
        # Compute CVaR as probability-weighted mean of tail
        # Identify tail scenarios (those with cost >= VaR)
        tail_scenarios = []
        tail_probability = 0.0
        tail_weighted_cost = 0.0
        
        for scenario in self.scenarios:
            s_cost = scenario_costs[scenario.id]
            if s_cost >= var_value - 1e-6:  # Include scenarios at or above VaR
                tail_scenarios.append(scenario.id)
                tail_probability += scenario.probability
                tail_weighted_cost += scenario.probability * s_cost
        
        # CVaR is the probability-weighted average of tail costs
        if tail_probability > 1e-9:
            cvar_value = tail_weighted_cost / tail_probability
        else:
            cvar_value = var_value  # Fallback if tail is empty
        
        # Verify CVaR >= VaR (mathematical property)
        if cvar_value < var_value - 1e-6:
            print(f"⚠️  Warning: CVaR ({cvar_value:.2f}) < VaR ({var_value:.2f}). Using VaR as CVaR.")
            cvar_value = var_value
        
        # Calculate equity measures
        satisfaction_ratios = []
        for scenario in self.scenarios:
            s = scenario.id
            for node in self.config.network.demand_nodes:
                demand = scenario.demand[node]
                unmet = scenario_unmet_demand[s][node]
                if demand > 0:
                    ratio = (demand - unmet) / demand
                    satisfaction_ratios.append(ratio)
        
        min_satisfaction_ratio = min(satisfaction_ratios) if satisfaction_ratios else 0.0
        avg_satisfaction_ratio = np.mean(satisfaction_ratios) if satisfaction_ratios else 0.0
        
        # Calculate capacity utilization metrics
        # Supplier utilization
        avg_supplier_utilization = {}
        for supplier in self.config.network.suppliers:
            total_usage = 0.0
            total_capacity = 0.0
            for scenario in self.scenarios:
                s = scenario.id
                # Sum outgoing flows from supplier
                supplier_flow = sum(
                    scenario_flows[s].get((supplier, target), 0.0)
                    for target in self.config.network.distribution_centers
                    if (supplier, target) in self.config.network.arcs
                )
                base_capacity = self.config.network.facilities[supplier]['capacity']
                capacity_factor = scenario.facility_capacity_factors[supplier]
                effective_capacity = base_capacity * capacity_factor
                
                total_usage += supplier_flow * scenario.probability
                total_capacity += effective_capacity * scenario.probability
            
            avg_supplier_utilization[supplier] = (total_usage / total_capacity * 100) if total_capacity > 0 else 0.0
        
        # DC utilization
        avg_dc_utilization = {}
        for dc in self.config.network.distribution_centers:
            storage_cap = self.config.network.facilities[dc]['storage_capacity']
            inventory = prepositioned_inventory[dc]
            avg_dc_utilization[dc] = (inventory / storage_cap * 100) if storage_cap > 0 else 0.0
        
        # Arc utilization
        avg_arc_utilization = {}
        for arc in self.config.network.arcs.keys():
            total_usage = 0.0
            total_capacity = 0.0
            for scenario in self.scenarios:
                s = scenario.id
                flow = scenario_flows[s].get(arc, 0.0)
                base_capacity = self.config.network.arcs[arc]['capacity']
                capacity_factor = scenario.arc_capacity_factors[arc]
                effective_capacity = base_capacity * capacity_factor
                
                total_usage += flow * scenario.probability
                total_capacity += effective_capacity * scenario.probability
            
            avg_arc_utilization[arc] = (total_usage / total_capacity * 100) if total_capacity > 0 else 0.0
        
        # Emergency procurement statistics
        scenarios_with_emergency = 0
        total_emergency_procurement = 0.0
        emergency_capacity_usage = {}
        
        for scenario in self.scenarios:
            s = scenario.id
            scenario_emergency = sum(scenario_emergency_procurement[s].values())
            if scenario_emergency > 1e-6:
                scenarios_with_emergency += 1
                total_emergency_procurement += scenario_emergency * scenario.probability
            
            # Track emergency capacity usage per supplier per scenario
            emergency_capacity_usage[s] = {}
            for supplier in self.config.network.suppliers:
                emergency_used = scenario_emergency_procurement[s].get(supplier, 0.0)
                supplier_capacity = self.config.network.facilities[supplier]['capacity']
                capacity_factor = scenario.facility_capacity_factors[supplier]
                effective_capacity = supplier_capacity * capacity_factor
                
                if effective_capacity > 1e-6:
                    usage_pct = (emergency_used / effective_capacity) * 100
                    emergency_capacity_usage[s][supplier] = usage_pct
                else:
                    emergency_capacity_usage[s][supplier] = 0.0
        
        # Identify binding constraints (within tolerance)
        tolerance = 1e-3  # Constraint is "tight" if slack < tolerance
        
        # Tight supplier capacity constraints
        tight_supplier_constraints = []
        for scenario in self.scenarios:
            s = scenario.id
            for supplier in self.config.network.suppliers:
                # Total outflow from supplier
                supplier_flow = sum(
                    scenario_flows[s].get((supplier, target), 0.0)
                    for target in self.config.network.distribution_centers
                    if (supplier, target) in self.config.network.arcs
                )
                # Add emergency procurement
                emergency = scenario_emergency_procurement[s].get(supplier, 0.0)
                total_usage = supplier_flow + emergency
                
                # Effective capacity
                base_capacity = self.config.network.facilities[supplier]['capacity']
                capacity_factor = scenario.facility_capacity_factors[supplier]
                effective_capacity = base_capacity * capacity_factor
                
                slack = effective_capacity - total_usage
                if slack < tolerance and effective_capacity > 1e-6:
                    tight_supplier_constraints.append((supplier, s, slack))
        
        # Tight DC storage constraints
        tight_dc_constraints = []
        for dc in self.config.network.distribution_centers:
            inventory = prepositioned_inventory[dc]
            storage_capacity = self.config.network.facilities[dc]['storage_capacity']
            slack = storage_capacity - inventory
            if slack < tolerance:
                tight_dc_constraints.append((dc, slack))
        
        # Tight arc capacity constraints
        tight_arc_constraints = []
        for scenario in self.scenarios:
            s = scenario.id
            for arc in self.config.network.arcs.keys():
                flow = scenario_flows[s].get(arc, 0.0)
                base_capacity = self.config.network.arcs[arc]['capacity']
                capacity_factor = scenario.arc_capacity_factors[arc]
                effective_capacity = base_capacity * capacity_factor
                
                slack = effective_capacity - flow
                if slack < tolerance and effective_capacity > 1e-6:
                    tight_arc_constraints.append((arc, s, slack))
        
        return OptimizationResult(
            status=status_str,
            objective_value=pulp.value(self.model.objective),
            solve_time=solve_time,
            prepositioned_inventory=prepositioned_inventory,
            scenario_costs=scenario_costs,
            scenario_flows=scenario_flows,
            scenario_unmet_demand=scenario_unmet_demand,
            scenario_emergency_procurement=scenario_emergency_procurement,
            expected_cost=expected_cost,
            cvar_value=cvar_value,
            var_value=var_value,
            tail_scenarios=tail_scenarios,
            tail_probability=tail_probability,
            min_satisfaction_ratio=min_satisfaction_ratio,
            avg_satisfaction_ratio=avg_satisfaction_ratio,
            avg_supplier_utilization=avg_supplier_utilization,
            avg_dc_utilization=avg_dc_utilization,
            avg_arc_utilization=avg_arc_utilization,
            scenarios_with_emergency=scenarios_with_emergency,
            total_emergency_procurement=total_emergency_procurement,
            tight_supplier_constraints=tight_supplier_constraints,
            tight_dc_constraints=tight_dc_constraints,
            tight_arc_constraints=tight_arc_constraints,
            emergency_capacity_usage=emergency_capacity_usage
        )
