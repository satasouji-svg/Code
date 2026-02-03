"""
Data validation module for ensuring input data integrity.

This module provides validation functions for all input data to prevent
numerical issues and ensure mathematical consistency.
"""

from typing import Dict, List, Tuple
import numpy as np
from config import Config
from scenario_generator import Scenario


class DataValidator:
    """Validates input data for the optimization model."""
    
    def __init__(self, config: Config):
        """
        Initialize data validator.
        
        Args:
            config: Configuration object to validate
        """
        self.config = config
        self.warnings: List[str] = []
        self.errors: List[str] = []
    
    def validate_all(self, scenarios: List[Scenario]) -> bool:
        """
        Perform comprehensive validation of all input data.
        
        Args:
            scenarios: List of scenarios to validate
            
        Returns:
            True if validation passes, False otherwise
        """
        self.warnings = []
        self.errors = []
        
        # Validate configuration
        try:
            self.config.validate()
        except AssertionError as e:
            self.errors.append(f"Configuration validation failed: {e}")
            return False
        
        # Validate network structure
        self._validate_network_structure()
        
        # Validate numerical scaling
        self._validate_numerical_scaling()
        
        # Validate scenarios
        self._validate_scenarios(scenarios)
        
        # Check for warnings
        if self.warnings:
            print("⚠️  Validation warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        # Check for errors
        if self.errors:
            print("❌ Validation errors:")
            for error in self.errors:
                print(f"  - {error}")
            return False
        
        print("✅ Data validation passed successfully")
        return True
    
    def _validate_network_structure(self):
        """Validate that network structure is well-formed."""
        suppliers = set(self.config.network.suppliers)
        dcs = set(self.config.network.distribution_centers)
        demands = set(self.config.network.demand_nodes)
        
        # Check for disconnected nodes
        arc_sources = set()
        arc_targets = set()
        
        for (source, target) in self.config.network.arcs.keys():
            arc_sources.add(source)
            arc_targets.add(target)
        
        # Suppliers should have outgoing arcs
        for supplier in suppliers:
            if supplier not in arc_sources:
                self.warnings.append(f"Supplier {supplier} has no outgoing arcs")
        
        # Demand nodes should have incoming arcs
        for demand in demands:
            if demand not in arc_targets:
                self.errors.append(f"Demand node {demand} has no incoming arcs")
        
        # DCs should be in the middle
        for dc in dcs:
            if dc not in arc_targets:
                self.warnings.append(f"DC {dc} has no incoming arcs")
            if dc not in arc_sources:
                self.warnings.append(f"DC {dc} has no outgoing arcs")
    
    def _validate_numerical_scaling(self):
        """Validate that numerical values are well-scaled."""
        # Check for very large or very small values that could cause numerical issues
        
        # Arc costs
        arc_costs = [data['cost'] for data in self.config.network.arcs.values()]
        if arc_costs:
            max_cost = max(arc_costs)
            min_cost = min(arc_costs)
            if max_cost / min_cost > 1000:
                self.warnings.append(
                    f"Large range in arc costs ({min_cost:.2f} to {max_cost:.2f}). "
                    "Consider normalizing."
                )
        
        # Capacities
        arc_capacities = [data['capacity'] for data in self.config.network.arcs.values()]
        if arc_capacities:
            max_cap = max(arc_capacities)
            min_cap = min(arc_capacities)
            if max_cap / min_cap > 1000:
                self.warnings.append(
                    f"Large range in arc capacities ({min_cap:.2f} to {max_cap:.2f}). "
                    "Consider normalizing."
                )
        
        # Check penalty scaling
        penalty = self.config.optimization.unmet_demand_penalty
        avg_cost = np.mean(arc_costs) if arc_costs else 1.0
        
        if penalty / avg_cost < 10:
            self.warnings.append(
                f"Unmet demand penalty ({penalty}) may be too small relative to "
                f"average arc cost ({avg_cost:.2f}). Unmet demand may occur too easily."
            )
    
    def _validate_scenarios(self, scenarios: List[Scenario]):
        """Validate scenario data."""
        if not scenarios:
            self.errors.append("No scenarios provided")
            return
        
        # Check probability sum
        total_prob = sum(s.probability for s in scenarios)
        if abs(total_prob - 1.0) > 1e-6:
            self.errors.append(
                f"Scenario probabilities sum to {total_prob:.6f}, not 1.0"
            )
        
        # Check for extremely low probabilities (numerical issues)
        for scenario in scenarios:
            if scenario.probability < 1e-10:
                self.warnings.append(
                    f"Scenario {scenario.id} has very low probability "
                    f"({scenario.probability:.2e})"
                )
        
        # Check demand consistency
        for scenario in scenarios:
            for node in self.config.network.demand_nodes:
                if node not in scenario.demand:
                    self.errors.append(
                        f"Scenario {scenario.id} missing demand for node {node}"
                    )
        
        # Check for extreme demand values
        all_demands = []
        for scenario in scenarios:
            all_demands.extend(scenario.demand.values())
        
        if all_demands:
            mean_demand = np.mean(all_demands)
            std_demand = np.std(all_demands)
            
            for scenario in scenarios:
                for node, demand in scenario.demand.items():
                    if abs(demand - mean_demand) > 5 * std_demand:
                        self.warnings.append(
                            f"Scenario {scenario.id} has extreme demand for {node}: "
                            f"{demand:.2f} (mean={mean_demand:.2f}, std={std_demand:.2f})"
                        )


def validate_data(config: Config, scenarios: List[Scenario]) -> bool:
    """
    Convenience function to validate data.
    
    Args:
        config: Configuration object
        scenarios: List of scenarios
        
    Returns:
        True if validation passes, False otherwise
    """
    validator = DataValidator(config)
    return validator.validate_all(scenarios)
