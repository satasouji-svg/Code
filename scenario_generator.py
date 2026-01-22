"""
Scenario generation module for stochastic optimization.

This module generates realistic scenarios for demand variations and
disruption events in the wildfire-resilient supply network.
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from config import Config


@dataclass
class Scenario:
    """Represents a single scenario with demand and disruption data."""
    
    id: int
    probability: float
    demand: Dict[str, float]  # Demand at each demand node
    arc_capacity_factors: Dict[Tuple[str, str], float]  # Capacity reduction factors (0-1)
    facility_capacity_factors: Dict[str, float]  # Facility capacity reduction factors (0-1)
    
    def __post_init__(self):
        """Validate scenario data."""
        assert 0 <= self.probability <= 1, "Probability must be in [0, 1]"
        assert all(v >= 0 for v in self.demand.values()), "Demand must be non-negative"
        assert all(0 <= v <= 1 for v in self.arc_capacity_factors.values()), \
            "Arc capacity factors must be in [0, 1]"
        assert all(0 <= v <= 1 for v in self.facility_capacity_factors.values()), \
            "Facility capacity factors must be in [0, 1]"


class ScenarioGenerator:
    """Generates scenarios for stochastic optimization."""
    
    def __init__(self, config: Config):
        """
        Initialize scenario generator.
        
        Args:
            config: Configuration object with network and scenario parameters
        """
        self.config = config
        self.rng = np.random.RandomState(config.scenario.random_seed)
    
    def generate_scenarios(self) -> List[Scenario]:
        """
        Generate all scenarios for the optimization problem.
        
        Returns:
            List of Scenario objects with equal probabilities
        """
        scenarios = []
        n_scenarios = self.config.scenario.n_scenarios
        probability = 1.0 / n_scenarios
        
        for i in range(n_scenarios):
            # Generate demand variation
            demand = self._generate_demand()
            
            # Generate disruption events
            arc_factors, facility_factors = self._generate_disruptions()
            
            scenario = Scenario(
                id=i,
                probability=probability,
                demand=demand,
                arc_capacity_factors=arc_factors,
                facility_capacity_factors=facility_factors
            )
            scenarios.append(scenario)
        
        return scenarios
    
    def _generate_demand(self) -> Dict[str, float]:
        """
        Generate demand for all demand nodes with random variation.
        
        Uses lognormal distribution to ensure positive demands with
        realistic variation patterns.
        
        Returns:
            Dictionary mapping demand nodes to demand values
        """
        demand = {}
        cv = self.config.scenario.demand_variability
        
        for node, base_demand in self.config.network.base_demand.items():
            # Use lognormal distribution for positive values
            # Parameters chosen to match desired mean and CV
            sigma = np.sqrt(np.log(1 + cv**2))
            mu = np.log(base_demand) - 0.5 * sigma**2
            
            demand[node] = self.rng.lognormal(mu, sigma)
        
        return demand
    
    def _generate_disruptions(self) -> Tuple[Dict, Dict]:
        """
        Generate disruption events for arcs and facilities.
        
        Disruptions are modeled as capacity reductions that occur with
        a certain probability, affected by the exposure factor of each
        arc or facility.
        
        Returns:
            Tuple of (arc_capacity_factors, facility_capacity_factors)
        """
        arc_factors = {}
        facility_factors = {}
        
        # Determine if this scenario has a disruption event
        has_disruption = self.rng.rand() < self.config.scenario.disruption_probability
        
        if has_disruption:
            # Generate arc disruptions
            for arc, arc_data in self.config.network.arcs.items():
                exposure = arc_data.get('exposure', 0.0)
                
                # Higher exposure means higher probability of being affected
                if self.rng.rand() < exposure:
                    # Capacity reduction based on severity range
                    severity_range = self.config.scenario.disruption_severity_range
                    reduction = self.rng.uniform(*severity_range)
                    arc_factors[arc] = 1.0 - reduction
                else:
                    arc_factors[arc] = 1.0
            
            # Generate facility disruptions
            for facility, facility_data in self.config.network.facilities.items():
                exposure = facility_data.get('exposure', 0.0)
                
                if self.rng.rand() < exposure:
                    severity_range = self.config.scenario.disruption_severity_range
                    reduction = self.rng.uniform(*severity_range)
                    facility_factors[facility] = 1.0 - reduction
                else:
                    facility_factors[facility] = 1.0
        else:
            # No disruption - all capacities at full
            for arc in self.config.network.arcs.keys():
                arc_factors[arc] = 1.0
            
            for facility in self.config.network.facilities.keys():
                facility_factors[facility] = 1.0
        
        return arc_factors, facility_factors


def generate_scenarios(config: Config) -> List[Scenario]:
    """
    Convenience function to generate scenarios.
    
    Args:
        config: Configuration object
        
    Returns:
        List of generated scenarios
    """
    generator = ScenarioGenerator(config)
    return generator.generate_scenarios()
