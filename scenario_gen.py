"""
Scenario generation module for wildfire-resilient supply network optimization.
Generates stochastic scenarios with demand surges, arc disruptions, and correlations.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from config import NetworkConfig, ScenarioParameters


class Scenario:
    """Represents a single scenario with demand and disruption realizations."""
    
    def __init__(self, scenario_id: int, probability: float):
        self.id = scenario_id
        self.probability = probability
        self.demand = {}  # Zone -> demand value
        self.arc_disruption = {}  # Arc -> disruption status (0=operational, 1=disrupted)
        self.arc_capacity_factor = {}  # Arc -> remaining capacity fraction
    
    def __repr__(self):
        return f"Scenario(id={self.id}, prob={self.probability:.3f})"


class ScenarioGenerator:
    """Generates scenarios for two-stage stochastic programming."""
    
    def __init__(self, network_config: NetworkConfig, scenario_params: ScenarioParameters):
        self.network = network_config
        self.params = scenario_params
        np.random.seed(scenario_params.random_seed)
    
    def generate_scenarios(self, num_scenarios: int) -> List[Scenario]:
        """Generate a set of scenarios with equal probability."""
        scenarios = []
        probability = 1.0 / num_scenarios
        
        for i in range(num_scenarios):
            scenario = Scenario(scenario_id=i, probability=probability)
            
            # Generate correlated demand surges
            scenario.demand = self._generate_demand_surges()
            
            # Generate arc disruptions
            scenario.arc_disruption, scenario.arc_capacity_factor = self._generate_arc_disruptions()
            
            scenarios.append(scenario)
        
        return scenarios
    
    def _generate_demand_surges(self) -> Dict[str, float]:
        """Generate correlated demand surges across zones."""
        zones = self.network.demand_zones
        n_zones = len(zones)
        
        # Create correlation matrix
        correlation_matrix = np.eye(n_zones)
        for i in range(n_zones):
            for j in range(i+1, n_zones):
                correlation_matrix[i, j] = self.params.demand_correlation
                correlation_matrix[j, i] = self.params.demand_correlation
        
        # Generate correlated random variables using Cholesky decomposition
        try:
            L = np.linalg.cholesky(correlation_matrix)
            z = np.random.randn(n_zones)
            correlated_random = L @ z
        except np.linalg.LinAlgError:
            # If correlation matrix is not positive definite, use uncorrelated
            correlated_random = np.random.randn(n_zones)
        
        # Convert to demand multipliers
        demand_surges = {}
        for idx, zone in enumerate(zones):
            # Map normal random to uniform range
            surge_factor = np.clip(
                1.0 + 0.3 * correlated_random[idx],
                self.params.demand_surge_min,
                self.params.demand_surge_max
            )
            demand_surges[zone] = self.network.base_demand[zone] * surge_factor
        
        return demand_surges
    
    def _generate_arc_disruptions(self) -> Tuple[Dict[Tuple, bool], Dict[Tuple, float]]:
        """Generate arc disruptions with spatial correlation for wildfire."""
        arc_disruption = {}
        arc_capacity_factor = {}
        
        all_arcs = (self.network.supplier_dc_arcs + 
                   self.network.dc_zone_arcs)
        
        if self.params.spatial_correlation:
            # Simulate wildfire as a spatial event
            wildfire_occurs = np.random.rand() < 0.3  # 30% chance of wildfire
            
            if wildfire_occurs:
                # Choose a random center for the wildfire
                wildfire_center_idx = np.random.randint(0, len(all_arcs))
                
                for idx, arc in enumerate(all_arcs):
                    # Calculate distance-based correlation
                    distance = abs(idx - wildfire_center_idx)
                    correlated_prob = (self.params.disruption_prob_base * 
                                     np.exp(-distance * self.params.correlation_distance_decay))
                    
                    is_disrupted = np.random.rand() < correlated_prob
                    arc_disruption[arc] = is_disrupted
                    
                    if is_disrupted:
                        # Random severity of disruption
                        severity = np.random.uniform(*self.params.disruption_severity_range)
                        arc_capacity_factor[arc] = 1.0 - severity
                    else:
                        arc_capacity_factor[arc] = 1.0
            else:
                # No wildfire - all arcs operational
                for arc in all_arcs:
                    arc_disruption[arc] = False
                    arc_capacity_factor[arc] = 1.0
        else:
            # Independent disruptions
            for arc in all_arcs:
                is_disrupted = np.random.rand() < self.params.disruption_prob_base
                arc_disruption[arc] = is_disrupted
                
                if is_disrupted:
                    severity = np.random.uniform(*self.params.disruption_severity_range)
                    arc_capacity_factor[arc] = 1.0 - severity
                else:
                    arc_capacity_factor[arc] = 1.0
        
        return arc_disruption, arc_capacity_factor
    
    def get_scenario_summary(self, scenarios: List[Scenario]) -> pd.DataFrame:
        """Generate a summary dataframe of all scenarios."""
        data = []
        for scenario in scenarios:
            row = {
                'scenario_id': scenario.id,
                'probability': scenario.probability,
                'total_demand': sum(scenario.demand.values()),
                'num_disruptions': sum(scenario.arc_disruption.values()),
            }
            # Add individual zone demands
            for zone, demand in scenario.demand.items():
                row[f'demand_{zone}'] = demand
            data.append(row)
        
        return pd.DataFrame(data)


def generate_baseline_scenarios(network_config: NetworkConfig) -> List[Scenario]:
    """Generate simple baseline scenarios for testing."""
    scenarios = []
    
    # Scenario 1: No disruption, base demand
    s1 = Scenario(scenario_id=0, probability=0.5)
    s1.demand = network_config.base_demand.copy()
    s1.arc_disruption = {arc: False for arc in 
                        (network_config.supplier_dc_arcs + 
                         network_config.dc_zone_arcs)}
    s1.arc_capacity_factor = {arc: 1.0 for arc in s1.arc_disruption.keys()}
    scenarios.append(s1)
    
    # Scenario 2: High disruption, surge demand
    s2 = Scenario(scenario_id=1, probability=0.5)
    s2.demand = {zone: demand * 1.3 for zone, demand in network_config.base_demand.items()}
    s2.arc_disruption = {arc: (np.random.rand() < 0.3) for arc in 
                        (network_config.supplier_dc_arcs + 
                         network_config.dc_zone_arcs)}
    s2.arc_capacity_factor = {arc: (0.5 if disrupted else 1.0) 
                             for arc, disrupted in s2.arc_disruption.items()}
    scenarios.append(s2)
    
    return scenarios
