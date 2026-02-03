"""
Stress scenario configurations for creating reviewer-proof resilience experiments.

This module implements the "stress ladder" with Low/Medium/High severity levels
using mixture distributions for demand and realistic disruption patterns.

Based on expert guidance for creating trade-offs and forcing resilience mechanisms.
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from config import Config, ScenarioConfig, OptimizationConfig, NetworkConfig
from scenario_generator import Scenario, ScenarioGenerator


@dataclass
class StressLevel:
    """Configuration for a specific stress level."""
    
    name: str
    
    # Demand shock mixture distribution
    # Format: [(probability, (min_mult, max_mult)), ...]
    demand_mixture: List[Tuple[float, Tuple[float, float]]] = field(default_factory=list)
    
    # Disruption severity ranges for different arc types
    supplier_capacity_range: Tuple[float, float] = (0.85, 1.00)
    dc_to_demand_range: Tuple[float, float] = (0.75, 1.00)
    supplier_to_dc_range: Tuple[float, float] = (0.80, 1.00)
    
    # Correlated disruption probabilities
    prob_dc_focused_disruption: float = 0.0  # Probability of hitting one DC hard
    prob_supplier_focused_disruption: float = 0.0  # Probability of hitting primary supplier hard
    
    # Cost and penalty adjustments
    unmet_penalty: float = 500.0  # Per unit penalty for unmet demand
    emergency_cost_multiplier: float = 2.5  # Multiplier on normal route cost
    holding_cost: float = 1.0  # Holding cost per unit


# Define the three stress levels
LOW_STRESS = StressLevel(
    name="Low",
    demand_mixture=[
        (0.75, (0.95, 1.15)),  # Normal variability
        (0.20, (1.15, 1.40)),  # Elevated demand
        (0.05, (1.40, 1.75)),  # Extreme tail
    ],
    supplier_capacity_range=(0.85, 1.00),
    dc_to_demand_range=(0.75, 1.00),
    supplier_to_dc_range=(0.80, 1.00),
    prob_dc_focused_disruption=0.15,
    prob_supplier_focused_disruption=0.10,
    unmet_penalty=80.0,  # 8-10× transport cost
    emergency_cost_multiplier=2.5,
    holding_cost=0.8,
)

MEDIUM_STRESS = StressLevel(
    name="Medium",
    demand_mixture=[
        (0.75, (0.95, 1.15)),  # Normal variability
        (0.20, (1.15, 1.40)),  # Elevated demand
        (0.05, (1.40, 1.75)),  # Extreme tail
    ],
    supplier_capacity_range=(0.65, 0.95),
    dc_to_demand_range=(0.55, 0.95),
    supplier_to_dc_range=(0.60, 0.95),
    prob_dc_focused_disruption=0.25,
    prob_supplier_focused_disruption=0.15,
    unmet_penalty=100.0,  # 10-12× transport cost
    emergency_cost_multiplier=2.5,
    holding_cost=1.0,
)

HIGH_STRESS = StressLevel(
    name="High",
    demand_mixture=[
        (0.75, (0.95, 1.15)),  # Normal variability
        (0.20, (1.15, 1.40)),  # Elevated demand
        (0.05, (1.40, 1.75)),  # Extreme tail
    ],
    supplier_capacity_range=(0.45, 0.85),
    dc_to_demand_range=(0.35, 0.85),
    supplier_to_dc_range=(0.40, 0.90),
    prob_dc_focused_disruption=0.35,
    prob_supplier_focused_disruption=0.25,
    unmet_penalty=120.0,  # 12-15× transport cost
    emergency_cost_multiplier=2.5,
    holding_cost=1.2,
)


class StressScenarioGenerator(ScenarioGenerator):
    """
    Extended scenario generator with stress levels and mixture distributions.
    
    Implements expert-recommended approach for creating realistic stress
    scenarios with trade-offs and visible resilience mechanisms.
    """
    
    def __init__(self, config: Config, stress_level: StressLevel = MEDIUM_STRESS):
        """
        Initialize stress scenario generator.
        
        Args:
            config: Configuration object
            stress_level: StressLevel object defining severity parameters
        """
        super().__init__(config)
        self.stress_level = stress_level
        
        # Validate mixture probabilities sum to 1
        total_prob = sum(p for p, _ in stress_level.demand_mixture)
        assert abs(total_prob - 1.0) < 1e-6, f"Demand mixture probabilities must sum to 1, got {total_prob}"
    
    def _generate_demand(self) -> Dict[str, float]:
        """
        Generate demand using mixture distribution for realistic tail events.
        
        This creates a proper right tail instead of pure uniform noise,
        which reviewers prefer for stress testing.
        
        Returns:
            Dictionary mapping demand nodes to demand values
        """
        demand = {}
        
        # Sample from mixture distribution
        r = self.rng.rand()
        cumulative_prob = 0.0
        selected_range = self.stress_level.demand_mixture[0][1]
        
        for prob, (min_mult, max_mult) in self.stress_level.demand_mixture:
            cumulative_prob += prob
            if r <= cumulative_prob:
                selected_range = (min_mult, max_mult)
                break
        
        # Generate demand for each node using selected range
        for node, base_demand in self.config.network.base_demand.items():
            multiplier = self.rng.uniform(*selected_range)
            demand[node] = base_demand * multiplier
        
        return demand
    
    def _generate_disruptions(self) -> Tuple[Dict, Dict]:
        """
        Generate disruptions with stress-level-specific severity ranges.
        
        Also implements correlated disruptions where one DC or supplier
        gets hit particularly hard in some scenarios.
        
        Returns:
            Tuple of (arc_capacity_factors, facility_capacity_factors)
        """
        arc_factors = {}
        facility_factors = {}
        
        # Determine disruption type
        has_dc_focus = self.rng.rand() < self.stress_level.prob_dc_focused_disruption
        has_supplier_focus = self.rng.rand() < self.stress_level.prob_supplier_focused_disruption
        
        # Generate facility disruptions first
        for facility, facility_data in self.config.network.facilities.items():
            if facility.startswith('S'):  # Supplier
                low, high = self.stress_level.supplier_capacity_range
                
                # Apply extra stress if this is a focused supplier disruption
                if has_supplier_focus and facility == 'S1':  # Hit primary supplier
                    reduction = self.rng.uniform(0.4, 0.7)  # Severe reduction
                else:
                    reduction = self.rng.uniform(1 - high, 1 - low)
                
                facility_factors[facility] = 1.0 - reduction
            else:  # DC
                # DCs get moderate disruptions (throughput constraints)
                reduction = self.rng.uniform(0.0, 0.15)
                
                # Apply extra stress if this is a focused DC disruption
                if has_dc_focus and facility == 'DC1':
                    reduction = self.rng.uniform(0.2, 0.4)
                
                facility_factors[facility] = 1.0 - reduction
        
        # Generate arc disruptions with stress-level ranges
        for arc, arc_data in self.config.network.arcs.items():
            source, dest = arc
            
            # Determine arc type and apply appropriate range
            if source.startswith('S') and dest.startswith('DC'):
                # Supplier → DC arc
                low, high = self.stress_level.supplier_to_dc_range
                reduction = self.rng.uniform(1 - high, 1 - low)
                
                # Extra stress if focused on this supplier
                if has_supplier_focus and source == 'S1':
                    reduction = self.rng.uniform(0.3, 0.6)
                
            elif source.startswith('DC') and dest.startswith('D'):
                # DC → Demand arc (hit hardest for last-mile disruption)
                low, high = self.stress_level.dc_to_demand_range
                reduction = self.rng.uniform(1 - high, 1 - low)
                
                # Extra stress if focused on this DC
                if has_dc_focus and source == 'DC1':
                    reduction = self.rng.uniform(0.45, 0.75)
            else:
                # Default case
                reduction = self.rng.uniform(0.0, 0.3)
            
            arc_factors[arc] = 1.0 - reduction
        
        return arc_factors, facility_factors
    
    def get_stress_description(self) -> str:
        """
        Get a detailed description of the stress level configuration.
        
        Returns:
            String describing the stress configuration
        """
        desc = f"""
Stress Level: {self.stress_level.name}
=======================================

Demand Mixture Distribution:
"""
        for i, (prob, (min_mult, max_mult)) in enumerate(self.stress_level.demand_mixture):
            desc += f"  {i+1}. {prob:.1%} probability: multiplier ∈ [{min_mult:.2f}, {max_mult:.2f}]\n"
        
        desc += f"""
Disruption Severity Ranges:
  - Supplier capacity: [{self.stress_level.supplier_capacity_range[0]:.2f}, {self.stress_level.supplier_capacity_range[1]:.2f}]
  - DC→Demand arcs: [{self.stress_level.dc_to_demand_range[0]:.2f}, {self.stress_level.dc_to_demand_range[1]:.2f}]
  - Supplier→DC arcs: [{self.stress_level.supplier_to_dc_range[0]:.2f}, {self.stress_level.supplier_to_dc_range[1]:.2f}]

Correlated Disruptions:
  - DC-focused disruption: {self.stress_level.prob_dc_focused_disruption:.1%} probability
  - Supplier-focused disruption: {self.stress_level.prob_supplier_focused_disruption:.1%} probability

Economic Parameters:
  - Unmet demand penalty: ${self.stress_level.unmet_penalty:.1f}/unit
  - Emergency cost multiplier: {self.stress_level.emergency_cost_multiplier:.1f}×
  - Holding cost: ${self.stress_level.holding_cost:.1f}/unit

Rationale:
  - Mixture distribution creates realistic tail events (not pure uniform)
  - Correlated disruptions create focused stress (not independent shocks)
  - Penalties calibrated to show trade-offs (not force 100% satisfaction)
"""
        return desc


def create_stress_config(stress_level: StressLevel, base_config: Config = None) -> Config:
    """
    Create a Config object with stress-level-specific parameters.
    
    Args:
        stress_level: StressLevel defining the severity
        base_config: Optional base configuration to modify
        
    Returns:
        Config object with adjusted parameters
    """
    if base_config is None:
        base_config = Config()
    
    # Create new config with adjusted optimization parameters
    new_opt_config = OptimizationConfig(
        cvar_alpha=base_config.optimization.cvar_alpha,
        cvar_weight=base_config.optimization.cvar_weight,
        expectation_weight=base_config.optimization.expectation_weight,
        min_demand_satisfaction=base_config.optimization.min_demand_satisfaction,
        unmet_demand_penalty=stress_level.unmet_penalty,
        inventory_holding_cost=stress_level.holding_cost,
        emergency_procurement_cost=base_config.optimization.emergency_procurement_cost,
        emergency_airlift_cost=base_config.optimization.emergency_airlift_cost * stress_level.emergency_cost_multiplier,
        emergency_airlift_capacity_per_supplier=base_config.optimization.emergency_airlift_capacity_per_supplier,
        emergency_arc_reliability=base_config.optimization.emergency_arc_reliability,
        emergency_capacity_fraction=base_config.optimization.emergency_capacity_fraction,
        leftover_disposal_cost=base_config.optimization.leftover_disposal_cost,
        big_m=base_config.optimization.big_m,
        tolerance=base_config.optimization.tolerance,
        equity_tolerance=base_config.optimization.equity_tolerance,
        solver_time_limit=base_config.optimization.solver_time_limit,
        solver_gap=base_config.optimization.solver_gap,
    )
    
    # Create new config
    new_config = Config(
        network=base_config.network,
        scenario=base_config.scenario,
        optimization=new_opt_config,
        scaling=base_config.scaling,
    )
    
    return new_config
