"""
Two-stage stochastic programming model for wildfire-resilient supply network.
Implements CVaR-based risk-averse optimization with equity constraints.
"""

import pyomo.environ as pyo
from typing import List, Dict, Tuple
from config import NetworkConfig, ModelParameters
from scenario_gen import Scenario


class WildfireSupplyNetworkModel:
    """Two-stage stochastic programming model with CVaR and equity."""
    
    def __init__(self, 
                 network_config: NetworkConfig,
                 model_params: ModelParameters,
                 scenarios: List[Scenario]):
        self.network = network_config
        self.params = model_params
        self.scenarios = scenarios
        self.model = None
    
    def build_model(self) -> pyo.ConcreteModel:
        """Build the complete two-stage stochastic programming model."""
        model = pyo.ConcreteModel(name="WildfireResilientSupplyNetwork")
        
        # Sets
        self._define_sets(model)
        
        # Parameters
        self._define_parameters(model)
        
        # First-stage decision variables
        self._define_first_stage_variables(model)
        
        # Second-stage decision variables (scenario-dependent)
        self._define_second_stage_variables(model)
        
        # CVaR variables
        self._define_cvar_variables(model)
        
        # Objective function
        self._define_objective(model)
        
        # First-stage constraints
        self._define_first_stage_constraints(model)
        
        # Second-stage constraints (for each scenario)
        self._define_second_stage_constraints(model)
        
        # CVaR constraints
        self._define_cvar_constraints(model)
        
        # Equity constraints
        self._define_equity_constraints(model)
        
        self.model = model
        return model
    
    def _define_sets(self, model):
        """Define sets for the model."""
        model.SUPPLIERS = pyo.Set(initialize=self.network.suppliers)
        model.DCS = pyo.Set(initialize=self.network.distribution_centers)
        model.ZONES = pyo.Set(initialize=self.network.demand_zones)
        model.SCENARIOS = pyo.Set(initialize=[s.id for s in self.scenarios])
        
        # Arc sets
        model.SUPPLIER_DC_ARCS = pyo.Set(initialize=self.network.supplier_dc_arcs, dimen=2)
        model.DC_ZONE_ARCS = pyo.Set(initialize=self.network.dc_zone_arcs, dimen=2)
        model.EMERGENCY_ARCS = pyo.Set(initialize=self.network.emergency_arcs, dimen=2)
        
        # All hardenable arcs (supplier-DC and DC-zone)
        model.HARDENABLE_ARCS = pyo.Set(
            initialize=self.network.supplier_dc_arcs + self.network.dc_zone_arcs,
            dimen=2
        )
    
    def _define_parameters(self, model):
        """Define parameters for the model."""
        # Supplier capacities
        model.supplier_capacity = pyo.Param(
            model.SUPPLIERS,
            initialize=self.network.supplier_capacity
        )
        
        # DC storage capacities
        model.dc_storage = pyo.Param(
            model.DCS,
            initialize=self.network.dc_storage_capacity
        )
        
        # Scenario probabilities
        model.scenario_prob = pyo.Param(
            model.SCENARIOS,
            initialize={s.id: s.probability for s in self.scenarios}
        )
        
        # Demand by scenario and zone
        demand_data = {}
        for s in self.scenarios:
            for zone in self.network.demand_zones:
                demand_data[s.id, zone] = s.demand.get(zone, 0)
        model.demand = pyo.Param(model.SCENARIOS, model.ZONES, initialize=demand_data)
        
        # Arc capacity factors by scenario (1.0 if operational, <1.0 if disrupted)
        capacity_data = {}
        for s in self.scenarios:
            for arc in self.network.supplier_dc_arcs + self.network.dc_zone_arcs:
                capacity_data[s.id, arc] = s.arc_capacity_factor.get(arc, 1.0)
        model.arc_capacity_factor = pyo.Param(
            model.SCENARIOS, model.HARDENABLE_ARCS,
            initialize=capacity_data
        )
        
        # Costs
        model.transport_cost = pyo.Param(
            model.SUPPLIER_DC_ARCS | model.DC_ZONE_ARCS | model.EMERGENCY_ARCS,
            initialize=self.network.transport_cost
        )
        
        model.hardening_cost = pyo.Param(
            model.HARDENABLE_ARCS,
            initialize=self.network.hardening_cost
        )
        
        model.prepositioning_cost = pyo.Param(
            model.DCS,
            initialize=self.network.prepositioning_cost
        )
        
        model.holding_cost = pyo.Param(
            model.DCS,
            initialize=self.network.holding_cost
        )
        
        model.shortage_penalty = pyo.Param(initialize=self.network.shortage_penalty)
    
    def _define_first_stage_variables(self, model):
        """Define first-stage decision variables (here-and-now decisions)."""
        # Arc hardening decisions (binary: 1 if arc is hardened)
        model.harden = pyo.Var(model.HARDENABLE_ARCS, within=pyo.Binary)
        
        # Prepositioning inventory at DCs (continuous, non-negative)
        model.preposition = pyo.Var(model.DCS, within=pyo.NonNegativeReals)
    
    def _define_second_stage_variables(self, model):
        """Define second-stage decision variables (wait-and-see decisions)."""
        # Flow on supplier-DC arcs
        model.flow_supplier_dc = pyo.Var(
            model.SCENARIOS, model.SUPPLIER_DC_ARCS,
            within=pyo.NonNegativeReals
        )
        
        # Flow on DC-zone arcs
        model.flow_dc_zone = pyo.Var(
            model.SCENARIOS, model.DC_ZONE_ARCS,
            within=pyo.NonNegativeReals
        )
        
        # Emergency flow (bypass DC)
        model.flow_emergency = pyo.Var(
            model.SCENARIOS, model.EMERGENCY_ARCS,
            within=pyo.NonNegativeReals
        )
        
        # Unmet demand (shortage)
        model.shortage = pyo.Var(
            model.SCENARIOS, model.ZONES,
            within=pyo.NonNegativeReals
        )
        
        # Inventory held at DCs
        model.inventory = pyo.Var(
            model.SCENARIOS, model.DCS,
            within=pyo.NonNegativeReals
        )
    
    def _define_cvar_variables(self, model):
        """Define CVaR-related variables."""
        # Value-at-Risk (VaR) at confidence level alpha
        model.var = pyo.Var(within=pyo.Reals)
        
        # Auxiliary variables for CVaR calculation
        model.cvar_excess = pyo.Var(model.SCENARIOS, within=pyo.NonNegativeReals)
    
    def _define_objective(self, model):
        """Define the risk-averse objective with CVaR."""
        def objective_rule(m):
            # First-stage costs
            hardening_total = sum(m.hardening_cost[arc] * m.harden[arc]
                                for arc in m.HARDENABLE_ARCS)
            prepositioning_total = sum(m.prepositioning_cost[dc] * m.preposition[dc]
                                      for dc in m.DCS)
            first_stage_cost = hardening_total + prepositioning_total
            
            # Expected second-stage cost
            expected_second_stage = sum(
                m.scenario_prob[s] * self._scenario_cost(m, s)
                for s in m.SCENARIOS
            )
            
            # CVaR term
            cvar = m.var + (1.0 / (1.0 - self.params.alpha_cvar)) * sum(
                m.scenario_prob[s] * m.cvar_excess[s] for s in m.SCENARIOS
            )
            
            # Risk-averse objective: (1-lambda)*E[cost] + lambda*CVaR
            lambda_risk = self.params.lambda_risk
            objective = (first_stage_cost + 
                        (1 - lambda_risk) * expected_second_stage +
                        lambda_risk * cvar)
            
            return objective
        
        model.objective = pyo.Objective(rule=objective_rule, sense=pyo.minimize)
    
    def _scenario_cost(self, m, s):
        """Calculate the cost for a specific scenario."""
        # Transportation costs
        transport = (
            sum(m.transport_cost[arc] * m.flow_supplier_dc[s, arc]
                for arc in m.SUPPLIER_DC_ARCS) +
            sum(m.transport_cost[arc] * m.flow_dc_zone[s, arc]
                for arc in m.DC_ZONE_ARCS) +
            sum(m.transport_cost[arc] * m.flow_emergency[s, arc]
                for arc in m.EMERGENCY_ARCS)
        )
        
        # Holding costs
        holding = sum(m.holding_cost[dc] * m.inventory[s, dc] for dc in m.DCS)
        
        # Shortage penalties
        shortage = sum(m.shortage_penalty * m.shortage[s, zone] for zone in m.ZONES)
        
        return transport + holding + shortage
    
    def _define_first_stage_constraints(self, model):
        """Define first-stage constraints."""
        # Hardening budget constraint
        def hardening_budget_rule(m):
            return sum(m.hardening_cost[arc] * m.harden[arc]
                      for arc in m.HARDENABLE_ARCS) <= self.params.hardening_budget
        model.hardening_budget_constraint = pyo.Constraint(rule=hardening_budget_rule)
        
        # Prepositioning capacity constraints
        def preposition_capacity_rule(m, dc):
            return m.preposition[dc] <= m.dc_storage[dc]
        model.preposition_capacity = pyo.Constraint(model.DCS, rule=preposition_capacity_rule)
    
    def _define_second_stage_constraints(self, model):
        """Define second-stage constraints for each scenario."""
        # Supplier capacity constraints
        def supplier_capacity_rule(m, s, supplier):
            outflow = sum(m.flow_supplier_dc[s, arc]
                         for arc in m.SUPPLIER_DC_ARCS if arc[0] == supplier)
            emergency_flow = sum(m.flow_emergency[s, arc]
                               for arc in m.EMERGENCY_ARCS if arc[0] == supplier)
            return outflow + emergency_flow <= m.supplier_capacity[supplier]
        model.supplier_capacity_constraint = pyo.Constraint(
            model.SCENARIOS, model.SUPPLIERS, rule=supplier_capacity_rule
        )
        
        # DC flow conservation constraints (corrected balance)
        def dc_balance_rule(m, s, dc):
            # Inflow from suppliers
            inflow = sum(m.flow_supplier_dc[s, arc]
                        for arc in m.SUPPLIER_DC_ARCS if arc[1] == dc)
            # Add prepositioned inventory
            inflow += m.preposition[dc]
            
            # Outflow to zones
            outflow = sum(m.flow_dc_zone[s, arc]
                         for arc in m.DC_ZONE_ARCS if arc[0] == dc)
            # Add inventory held at DC
            outflow += m.inventory[s, dc]
            
            return inflow == outflow
        model.dc_balance = pyo.Constraint(
            model.SCENARIOS, model.DCS, rule=dc_balance_rule
        )
        
        # Demand satisfaction constraints
        def demand_satisfaction_rule(m, s, zone):
            # Regular flow from DCs
            inflow_dc = sum(m.flow_dc_zone[s, arc]
                           for arc in m.DC_ZONE_ARCS if arc[1] == zone)
            # Emergency flow
            inflow_emergency = sum(m.flow_emergency[s, arc]
                                  for arc in m.EMERGENCY_ARCS if arc[1] == zone)
            
            return inflow_dc + inflow_emergency + m.shortage[s, zone] >= m.demand[s, zone]
        model.demand_satisfaction = pyo.Constraint(
            model.SCENARIOS, model.ZONES, rule=demand_satisfaction_rule
        )
        
        # Arc capacity constraints with hardening effects
        def arc_capacity_rule(m, s, arc):
            # Effective capacity factor: if hardened, disruption impact is reduced
            if arc in m.SUPPLIER_DC_ARCS:
                base_factor = m.arc_capacity_factor[s, arc]
                # Hardening improves resilience
                effective_factor = base_factor + m.harden[arc] * (1.0 - base_factor) * 0.7
                # Large M for capacity limit (no explicit capacity on arcs)
                return m.flow_supplier_dc[s, arc] <= 1000 * effective_factor
            else:
                return pyo.Constraint.Skip
        model.supplier_dc_arc_capacity = pyo.Constraint(
            model.SCENARIOS, model.SUPPLIER_DC_ARCS, rule=arc_capacity_rule
        )
        
        def dc_zone_arc_capacity_rule(m, s, arc):
            base_factor = m.arc_capacity_factor[s, arc]
            effective_factor = base_factor + m.harden[arc] * (1.0 - base_factor) * 0.7
            return m.flow_dc_zone[s, arc] <= 1000 * effective_factor
        model.dc_zone_arc_capacity = pyo.Constraint(
            model.SCENARIOS, model.DC_ZONE_ARCS, rule=dc_zone_arc_capacity_rule
        )
        
        # Storage capacity at DCs
        def storage_capacity_rule(m, s, dc):
            return m.inventory[s, dc] <= m.dc_storage[dc]
        model.storage_capacity = pyo.Constraint(
            model.SCENARIOS, model.DCS, rule=storage_capacity_rule
        )
    
    def _define_cvar_constraints(self, model):
        """Define CVaR constraints."""
        def cvar_excess_rule(m, s):
            scenario_cost = self._scenario_cost(m, s)
            return m.cvar_excess[s] >= scenario_cost - m.var
        model.cvar_excess_constraint = pyo.Constraint(
            model.SCENARIOS, rule=cvar_excess_rule
        )
    
    def _define_equity_constraints(self, model):
        """Define equity constraints based on mode."""
        if self.params.equity_mode == 1:
            # Mode 1: Minimum service level constraint
            def min_service_rule(m, s, zone):
                inflow_dc = sum(m.flow_dc_zone[s, arc]
                               for arc in m.DC_ZONE_ARCS if arc[1] == zone)
                inflow_emergency = sum(m.flow_emergency[s, arc]
                                      for arc in m.EMERGENCY_ARCS if arc[1] == zone)
                total_service = inflow_dc + inflow_emergency
                return total_service >= self.params.beta_min_service * m.demand[s, zone]
            model.min_service_constraint = pyo.Constraint(
                model.SCENARIOS, model.ZONES, rule=min_service_rule
            )
        
        elif self.params.equity_mode == 2:
            # Mode 2: Minimize inequity (via auxiliary variables)
            # Add variables for service level deviation
            model.service_level = pyo.Var(
                model.SCENARIOS, model.ZONES,
                within=pyo.NonNegativeReals, bounds=(0, 1)
            )
            
            model.max_service_level = pyo.Var(model.SCENARIOS, within=pyo.NonNegativeReals)
            model.min_service_level = pyo.Var(model.SCENARIOS, within=pyo.NonNegativeReals)
            
            # Calculate service level
            def service_level_rule(m, s, zone):
                inflow_dc = sum(m.flow_dc_zone[s, arc]
                               for arc in m.DC_ZONE_ARCS if arc[1] == zone)
                inflow_emergency = sum(m.flow_emergency[s, arc]
                                      for arc in m.EMERGENCY_ARCS if arc[1] == zone)
                total_service = inflow_dc + inflow_emergency
                # Service level = served / demand
                return m.service_level[s, zone] * m.demand[s, zone] == total_service
            model.service_level_def = pyo.Constraint(
                model.SCENARIOS, model.ZONES, rule=service_level_rule
            )
            
            # Track max and min service levels
            def max_service_rule(m, s, zone):
                return m.max_service_level[s] >= m.service_level[s, zone]
            model.max_service_constraint = pyo.Constraint(
                model.SCENARIOS, model.ZONES, rule=max_service_rule
            )
            
            def min_service_rule(m, s, zone):
                return m.min_service_level[s] <= m.service_level[s, zone]
            model.min_service_constraint = pyo.Constraint(
                model.SCENARIOS, model.ZONES, rule=min_service_rule
            )
