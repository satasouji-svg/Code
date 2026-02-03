"""
Configuration module for the wildfire-resilient supply network optimization model.

This module defines all parameters, network topology, and scenario configurations
for the two-stage stochastic MILP optimization problem.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import numpy as np


@dataclass
class NetworkConfig:
    """Configuration for network topology and base parameters."""
    
    # Network nodes
    suppliers: List[str] = field(default_factory=lambda: ['S1', 'S2', 'S3'])
    distribution_centers: List[str] = field(default_factory=lambda: ['DC1', 'DC2'])
    demand_nodes: List[str] = field(default_factory=lambda: ['D1', 'D2', 'D3', 'D4'])
    
    # Network arcs (source, destination) with base capacities and costs
    arcs: Dict[Tuple[str, str], Dict] = field(default_factory=lambda: {
        # Supplier to DC arcs
        ('S1', 'DC1'): {'capacity': 1000.0, 'cost': 5.0, 'exposure': 0.2},
        ('S1', 'DC2'): {'capacity': 800.0, 'cost': 7.0, 'exposure': 0.3},
        ('S2', 'DC1'): {'capacity': 900.0, 'cost': 6.0, 'exposure': 0.25},
        ('S2', 'DC2'): {'capacity': 1000.0, 'cost': 5.5, 'exposure': 0.15},
        ('S3', 'DC1'): {'capacity': 700.0, 'cost': 8.0, 'exposure': 0.4},
        ('S3', 'DC2'): {'capacity': 850.0, 'cost': 6.5, 'exposure': 0.35},
        # DC to demand arcs
        ('DC1', 'D1'): {'capacity': 500.0, 'cost': 3.0, 'exposure': 0.1},
        ('DC1', 'D2'): {'capacity': 450.0, 'cost': 3.5, 'exposure': 0.15},
        ('DC1', 'D3'): {'capacity': 400.0, 'cost': 4.0, 'exposure': 0.2},
        ('DC1', 'D4'): {'capacity': 350.0, 'cost': 4.5, 'exposure': 0.25},
        ('DC2', 'D1'): {'capacity': 450.0, 'cost': 4.0, 'exposure': 0.2},
        ('DC2', 'D2'): {'capacity': 500.0, 'cost': 3.5, 'exposure': 0.15},
        ('DC2', 'D3'): {'capacity': 480.0, 'cost': 3.0, 'exposure': 0.1},
        ('DC2', 'D4'): {'capacity': 400.0, 'cost': 4.2, 'exposure': 0.18},
    })
    
    # Facility parameters
    facilities: Dict[str, Dict] = field(default_factory=lambda: {
        'S1': {'capacity': 2000.0, 'exposure': 0.15, 'preposition_cost': 2.0},
        'S2': {'capacity': 1800.0, 'exposure': 0.2, 'preposition_cost': 2.5},
        'S3': {'capacity': 1600.0, 'exposure': 0.3, 'preposition_cost': 3.0},
        'DC1': {'storage_capacity': 1500.0, 'exposure': 0.1, 'holding_cost': 1.0},
        'DC2': {'storage_capacity': 1500.0, 'exposure': 0.12, 'holding_cost': 1.2},
    })
    
    # Base demand for each demand node (nominal)
    base_demand: Dict[str, float] = field(default_factory=lambda: {
        'D1': 300.0,
        'D2': 350.0,
        'D3': 280.0,
        'D4': 320.0,
    })


@dataclass
class ScenarioConfig:
    """Configuration for stochastic scenarios."""
    
    # Number of scenarios (increased to 100 for proper CVaR tail representation)
    n_scenarios: int = 100
    
    # Scenario generation parameters
    demand_variability: float = 0.3  # Coefficient of variation for demand
    disruption_probability: float = 0.4  # Probability of disruption per scenario
    disruption_severity_range: Tuple[float, float] = (0.3, 0.8)  # Range of capacity reduction
    
    # Demand shock capping (winsorization) - limits extreme tail events
    # Cap demand at mean + max_sigma_deviation * std_dev
    max_sigma_deviation: float = 3.5  # Maximum standard deviations from mean (stress-testing level)
    
    # Random seed for reproducibility
    random_seed: int = 42


@dataclass
class ScalingConfig:
    """Configuration for cost/distance scaling and units."""
    
    # Define what "1 unit" represents in the model
    cost_unit: str = "$1,000 CAD"  # What 1 cost unit represents
    distance_unit: str = "100 km"   # What 1 distance unit represents  
    quantity_unit: str = "pallets"  # What 1 quantity unit represents
    
    # Scaling factors for transparent mapping (model value → real value)
    cost_scale_factor: float = 1000.0    # Model $1 = Real $1,000 CAD
    distance_scale_factor: float = 100.0  # Model 1 = Real 100 km
    quantity_scale_factor: float = 1.0    # Model 1 = Real 1 pallet (no scaling)
    
    # Explanation for reviewers
    scaling_rationale: str = (
        "Costs scaled by 1000× for numerical stability. All reported values use model units. "
        "Mapping: Model $1 = Real $1,000 CAD. Economic trade-offs preserved."
    )
    
    def to_real_cost(self, model_cost: float) -> float:
        """Convert model cost to real CAD dollars."""
        return model_cost * self.cost_scale_factor
    
    def to_real_distance(self, model_distance: float) -> float:
        """Convert model distance to real kilometers."""
        return model_distance * self.distance_scale_factor


@dataclass
class OptimizationConfig:
    """Configuration for optimization model parameters."""
    
    # CVaR parameters (adjusted for better tail representation with more scenarios)
    cvar_alpha: float = 0.90  # Confidence level for CVaR (90th percentile)
    cvar_weight: float = 0.3  # Weight of CVaR in objective (0-1)
    expectation_weight: float = 0.7  # Weight of expected cost (should sum to 1 with cvar_weight)
    
    # Equity parameters
    min_demand_satisfaction: float = 0.75  # Minimum fraction of demand that must be satisfied
    # Note: equity_penalty removed - equity is enforced as hard constraint, not penalized
    
    # Penalty parameters (properly scaled to avoid inflation)
    unmet_demand_penalty: float = 500.0  # Per unit penalty for unmet demand
    
    # First stage costs
    inventory_holding_cost: float = 1.5  # Cost per unit of prepositioned inventory
    
    # Second stage costs (recourse)
    emergency_procurement_cost: float = 20.0  # Cost per unit of emergency procurement (LEGACY - not used with airlift)
    
    # Q1 CRITICAL FIX: Emergency as airlift/direct shipping
    # Emergency is now modeled as direct supplier→demand arcs (airlift)
    emergency_airlift_cost: float = 50.0  # Cost per unit for emergency airlift (higher than regular transport)
    emergency_airlift_capacity_per_supplier: float = 500.0  # Max emergency capacity per supplier
    emergency_arc_reliability: float = 0.95  # Emergency arcs have high reliability (minimal disruption)
    
    # Emergency procurement limits (Q1 fix: add explicit caps)
    # Emergency capacity as fraction of base supplier capacity
    emergency_capacity_fraction: float = 0.5  # Emergency can provide up to 50% of base capacity (LEGACY)
    leftover_disposal_cost: float = 0.5  # Cost per unit of leftover inventory (optional penalty)
    
    # Numerical stability parameters
    big_m: float = 1e6  # Big-M value for logical constraints
    tolerance: float = 1e-6  # Numerical tolerance for constraint violations
    equity_tolerance: float = 1e-6  # Tolerance for equity constraint satisfaction checks
    
    # Solver parameters (PERFORMANCE FIX: practical gap for stable, reliable solutions)
    solver_time_limit: int = 300  # Maximum solver time in seconds
    solver_gap: float = 1e-4  # MIP gap tolerance (practical balance of quality and speed)
    # Note: 1e-6 gap causes CBC to grind on tiny improvements and creates instability
    # Use 1e-3 for pilot runs, 1e-4 for production, 1e-5 only if truly needed
    
    def validate(self):
        """Validate configuration parameters."""
        assert 0 < self.cvar_alpha < 1, "CVaR alpha must be in (0, 1)"
        assert abs(self.cvar_weight + self.expectation_weight - 1.0) < 1e-6, \
            "CVaR weight and expectation weight must sum to 1"
        assert 0 <= self.min_demand_satisfaction <= 1, \
            "Minimum demand satisfaction must be in [0, 1]"
        assert self.unmet_demand_penalty > 0, "Unmet demand penalty must be positive"
        assert self.emergency_procurement_cost > 0, "Emergency procurement cost must be positive"


@dataclass
class Config:
    """Master configuration containing all sub-configurations."""
    
    network: NetworkConfig = field(default_factory=NetworkConfig)
    scenario: ScenarioConfig = field(default_factory=ScenarioConfig)
    optimization: OptimizationConfig = field(default_factory=OptimizationConfig)
    scaling: ScalingConfig = field(default_factory=ScalingConfig)
    
    def validate(self):
        """Validate all configuration parameters."""
        self.optimization.validate()
        
        # Validate network configuration
        assert len(self.network.suppliers) > 0, "Must have at least one supplier"
        assert len(self.network.distribution_centers) > 0, "Must have at least one DC"
        assert len(self.network.demand_nodes) > 0, "Must have at least one demand node"
        assert len(self.network.arcs) > 0, "Must have at least one arc"
        
        # Validate scenario configuration
        assert self.scenario.n_scenarios > 0, "Must have at least one scenario"
        assert 0 < self.scenario.demand_variability < 1, "Demand variability must be in (0, 1)"
        assert 0 <= self.scenario.disruption_probability <= 1, \
            "Disruption probability must be in [0, 1]"


def get_default_config() -> Config:
    """Return a default configuration instance."""
    config = Config()
    config.validate()
    return config
