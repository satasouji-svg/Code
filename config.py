"""
Configuration module for wildfire-resilient supply network optimization.
Defines network structure, costs, and model parameters.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional


class NetworkConfig:
    """Configuration for the supply network topology and parameters."""
    
    def __init__(self):
        # Network structure
        self.suppliers = ['S1', 'S2', 'S3']
        self.distribution_centers = ['DC1', 'DC2', 'DC3']
        self.demand_zones = ['Z1', 'Z2', 'Z3', 'Z4']
        
        # Supplier capacities (tons per period)
        self.supplier_capacity = {
            'S1': 100,
            'S2': 120,
            'S3': 80
        }
        
        # Distribution center storage capacities
        self.dc_storage_capacity = {
            'DC1': 150,
            'DC2': 120,
            'DC3': 100
        }
        
        # Base demand for each zone (tons per period)
        self.base_demand = {
            'Z1': 40,
            'Z2': 50,
            'Z3': 45,
            'Z4': 35
        }
        
        # Network arcs: (from, to) pairs
        # Supplier to DC arcs
        self.supplier_dc_arcs = [
            ('S1', 'DC1'), ('S1', 'DC2'),
            ('S2', 'DC2'), ('S2', 'DC3'),
            ('S3', 'DC1'), ('S3', 'DC3')
        ]
        
        # DC to demand zone arcs
        self.dc_zone_arcs = [
            ('DC1', 'Z1'), ('DC1', 'Z2'),
            ('DC2', 'Z1'), ('DC2', 'Z2'), ('DC2', 'Z3'),
            ('DC3', 'Z2'), ('DC3', 'Z3'), ('DC3', 'Z4')
        ]
        
        # Emergency direct arcs (bypass DCs in emergencies)
        self.emergency_arcs = [
            ('S1', 'Z1'), ('S2', 'Z2'), ('S3', 'Z4')
        ]
        
        # Transportation costs ($ per ton)
        self.transport_cost = {}
        for arc in self.supplier_dc_arcs:
            self.transport_cost[arc] = np.random.uniform(5, 15)
        for arc in self.dc_zone_arcs:
            self.transport_cost[arc] = np.random.uniform(3, 10)
        for arc in self.emergency_arcs:
            self.transport_cost[arc] = np.random.uniform(20, 40)  # Higher emergency cost
        
        # Arc hardening costs ($ per arc) - first-stage decision
        self.hardening_cost = {}
        for arc in self.supplier_dc_arcs + self.dc_zone_arcs:
            self.hardening_cost[arc] = np.random.uniform(1000, 5000)
        
        # Prepositioning costs at DCs ($ per ton) - first-stage decision
        self.prepositioning_cost = {
            'DC1': 2.0,
            'DC2': 2.5,
            'DC3': 2.2
        }
        
        # Inventory holding costs at DCs ($ per ton per period)
        self.holding_cost = {
            'DC1': 1.0,
            'DC2': 1.2,
            'DC3': 1.1
        }
        
        # Unmet demand penalty ($ per ton) - high to encourage service
        self.shortage_penalty = 1000.0


class ModelParameters:
    """Parameters for the two-stage stochastic programming model."""
    
    def __init__(self):
        # Risk aversion parameter (lambda) - weight on CVaR
        self.lambda_risk = 0.5  # Range: [0, 1], 0=risk-neutral, 1=fully risk-averse
        
        # CVaR confidence level (alpha) - tail probability
        self.alpha_cvar = 0.95  # Common values: 0.90, 0.95, 0.99
        
        # Equity mode and parameters
        self.equity_mode = 1  # 1 = minimum service level, 2 = minimize inequity
        
        # Minimum service level (beta) for Mode 1 - fraction of demand to be met
        self.beta_min_service = 0.80  # Range: [0, 1]
        
        # Hardening budget limit ($)
        self.hardening_budget = 15000.0
        
        # Number of scenarios
        self.num_scenarios = 20
        
        # Scenario generation parameters
        self.demand_surge_mean = 1.2  # Mean demand multiplier
        self.demand_surge_std = 0.15   # Std dev of demand multiplier
        self.arc_disruption_prob = 0.15  # Base probability of arc disruption
        self.hardening_reduction = 0.7   # Disruption probability reduction with hardening


class ScenarioParameters:
    """Parameters for scenario generation."""
    
    def __init__(self):
        # Demand uncertainty
        self.demand_correlation = 0.3  # Correlation between zone demands
        self.demand_surge_min = 1.0
        self.demand_surge_max = 1.5
        
        # Arc disruption parameters
        self.disruption_prob_base = 0.15
        self.disruption_severity_range = (0.0, 1.0)  # Fraction of capacity lost
        
        # Wildfire correlation
        self.spatial_correlation = True  # Enable spatial correlation for wildfire
        self.correlation_distance_decay = 0.5  # Decay factor for spatial correlation
        
        # Random seed for reproducibility
        self.random_seed = 42


def get_default_config() -> Tuple[NetworkConfig, ModelParameters, ScenarioParameters]:
    """Get default configuration for the optimization model."""
    return NetworkConfig(), ModelParameters(), ScenarioParameters()
