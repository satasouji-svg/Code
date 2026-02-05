"""
Test suite for wildfire-resilient supply network optimization.
Tests model structure, scenario generation, solution validation, and edge cases.
"""

import pytest
import numpy as np
from config import NetworkConfig, ModelParameters, ScenarioParameters, get_default_config
from scenario_gen import ScenarioGenerator, Scenario
from model import WildfireSupplyNetworkModel
from solver import OptimizationSolver
from validation import ModelValidator


class TestConfiguration:
    """Test configuration modules."""
    
    def test_default_config_creation(self):
        """Test that default configuration is created properly."""
        network_config, model_params, scenario_params = get_default_config()
        
        assert len(network_config.suppliers) > 0
        assert len(network_config.distribution_centers) > 0
        assert len(network_config.demand_zones) > 0
        assert model_params.lambda_risk >= 0 and model_params.lambda_risk <= 1
        assert model_params.alpha_cvar >= 0 and model_params.alpha_cvar <= 1
    
    def test_network_structure_consistency(self):
        """Test that network arcs are consistent."""
        config = NetworkConfig()
        
        # Check supplier-DC arcs reference valid nodes
        for arc in config.supplier_dc_arcs:
            assert arc[0] in config.suppliers
            assert arc[1] in config.distribution_centers
        
        # Check DC-zone arcs reference valid nodes
        for arc in config.dc_zone_arcs:
            assert arc[0] in config.distribution_centers
            assert arc[1] in config.demand_zones


class TestScenarioGeneration:
    """Test scenario generation module."""
    
    def test_scenario_probability_sum(self):
        """Test that scenario probabilities sum to 1."""
        network_config, _, scenario_params = get_default_config()
        gen = ScenarioGenerator(network_config, scenario_params)
        
        scenarios = gen.generate_scenarios(10)
        prob_sum = sum(s.probability for s in scenarios)
        
        assert abs(prob_sum - 1.0) < 1e-6
    
    def test_scenario_demand_generation(self):
        """Test that demands are generated for all zones."""
        network_config, _, scenario_params = get_default_config()
        gen = ScenarioGenerator(network_config, scenario_params)
        
        scenarios = gen.generate_scenarios(5)
        
        for scenario in scenarios:
            assert len(scenario.demand) == len(network_config.demand_zones)
            for zone in network_config.demand_zones:
                assert zone in scenario.demand
                assert scenario.demand[zone] > 0
    
    def test_scenario_arc_disruptions(self):
        """Test that arc disruptions are generated."""
        network_config, _, scenario_params = get_default_config()
        gen = ScenarioGenerator(network_config, scenario_params)
        
        scenarios = gen.generate_scenarios(5)
        
        for scenario in scenarios:
            assert len(scenario.arc_disruption) > 0
            assert len(scenario.arc_capacity_factor) > 0
            
            # Check capacity factors are in valid range
            for arc, factor in scenario.arc_capacity_factor.items():
                assert 0 <= factor <= 1.0
    
    def test_demand_correlation(self):
        """Test that demand correlation is applied."""
        network_config, _, scenario_params = get_default_config()
        scenario_params.demand_correlation = 0.8
        gen = ScenarioGenerator(network_config, scenario_params)
        
        scenarios = gen.generate_scenarios(100)
        
        # Extract demand variations
        zone1_demands = [s.demand[network_config.demand_zones[0]] for s in scenarios]
        zone2_demands = [s.demand[network_config.demand_zones[1]] for s in scenarios]
        
        # Check that demands vary (not all the same)
        assert len(set(zone1_demands)) > 1


class TestModelBuilding:
    """Test model construction."""
    
    def test_model_builds_successfully(self):
        """Test that model builds without errors."""
        network_config, model_params, scenario_params = get_default_config()
        gen = ScenarioGenerator(network_config, scenario_params)
        scenarios = gen.generate_scenarios(5)
        
        model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
        pyomo_model = model.build_model()
        
        assert pyomo_model is not None
        assert hasattr(pyomo_model, 'objective')
    
    def test_model_has_required_variables(self):
        """Test that model has all required variables."""
        network_config, model_params, scenario_params = get_default_config()
        gen = ScenarioGenerator(network_config, scenario_params)
        scenarios = gen.generate_scenarios(5)
        
        model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
        pyomo_model = model.build_model()
        
        # First-stage variables
        assert hasattr(pyomo_model, 'harden')
        assert hasattr(pyomo_model, 'preposition')
        
        # Second-stage variables
        assert hasattr(pyomo_model, 'flow_supplier_dc')
        assert hasattr(pyomo_model, 'flow_dc_zone')
        assert hasattr(pyomo_model, 'shortage')
        
        # CVaR variables
        assert hasattr(pyomo_model, 'var')
        assert hasattr(pyomo_model, 'cvar_excess')
    
    def test_model_has_required_constraints(self):
        """Test that model has all required constraints."""
        network_config, model_params, scenario_params = get_default_config()
        gen = ScenarioGenerator(network_config, scenario_params)
        scenarios = gen.generate_scenarios(5)
        
        model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
        pyomo_model = model.build_model()
        
        assert hasattr(pyomo_model, 'hardening_budget_constraint')
        assert hasattr(pyomo_model, 'supplier_capacity_constraint')
        assert hasattr(pyomo_model, 'dc_balance')
        assert hasattr(pyomo_model, 'demand_satisfaction')
        assert hasattr(pyomo_model, 'cvar_excess_constraint')


class TestSolver:
    """Test solver functionality."""
    
    def test_solver_initialization(self):
        """Test that solver initializes correctly."""
        solver = OptimizationSolver()
        assert solver is not None
    
    def test_small_model_solves(self):
        """Test that a small model can be solved."""
        network_config, model_params, scenario_params = get_default_config()
        gen = ScenarioGenerator(network_config, scenario_params)
        scenarios = gen.generate_scenarios(3)  # Small number for quick test
        
        model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
        pyomo_model = model.build_model()
        
        solver = OptimizationSolver()
        solution = solver.solve(pyomo_model)
        
        assert solution is not None
        assert 'status' in solution
        assert solution['solve_time'] > 0


class TestValidation:
    """Test validation module."""
    
    def test_validator_creation(self):
        """Test validator initialization."""
        validator = ModelValidator()
        assert validator is not None
    
    def test_probability_validation(self):
        """Test probability sum validation."""
        scenarios = [
            Scenario(0, 0.5),
            Scenario(1, 0.5)
        ]
        
        validator = ModelValidator()
        result = validator.validate_scenario_probabilities(scenarios)
        
        assert result['valid'] is True
    
    def test_invalid_probability_sum(self):
        """Test that invalid probabilities are caught."""
        scenarios = [
            Scenario(0, 0.3),
            Scenario(1, 0.5)
        ]
        
        validator = ModelValidator()
        result = validator.validate_scenario_probabilities(scenarios)
        
        assert result['valid'] is False
        assert len(result['errors']) > 0
    
    def test_model_structure_validation(self):
        """Test model structure validation."""
        network_config, model_params, scenario_params = get_default_config()
        gen = ScenarioGenerator(network_config, scenario_params)
        scenarios = gen.generate_scenarios(3)
        
        model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
        pyomo_model = model.build_model()
        
        validator = ModelValidator()
        result = validator.validate_model_structure(pyomo_model)
        
        assert result['valid'] is True
        assert len(result['checks']) > 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_hardening_budget(self):
        """Test model with zero hardening budget."""
        network_config, model_params, scenario_params = get_default_config()
        model_params.hardening_budget = 0.0
        
        gen = ScenarioGenerator(network_config, scenario_params)
        scenarios = gen.generate_scenarios(3)
        
        model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
        pyomo_model = model.build_model()
        
        assert pyomo_model is not None
    
    def test_risk_neutral_model(self):
        """Test risk-neutral model (lambda=0)."""
        network_config, model_params, scenario_params = get_default_config()
        model_params.lambda_risk = 0.0
        
        gen = ScenarioGenerator(network_config, scenario_params)
        scenarios = gen.generate_scenarios(3)
        
        model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
        pyomo_model = model.build_model()
        
        assert pyomo_model is not None
    
    def test_fully_risk_averse_model(self):
        """Test fully risk-averse model (lambda=1)."""
        network_config, model_params, scenario_params = get_default_config()
        model_params.lambda_risk = 1.0
        
        gen = ScenarioGenerator(network_config, scenario_params)
        scenarios = gen.generate_scenarios(3)
        
        model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
        pyomo_model = model.build_model()
        
        assert pyomo_model is not None
    
    def test_high_demand_scenario(self):
        """Test model with extremely high demand."""
        network_config, model_params, scenario_params = get_default_config()
        
        # Create scenarios with very high demand
        gen = ScenarioGenerator(network_config, scenario_params)
        scenario_params.demand_surge_max = 3.0  # 3x base demand
        scenarios = gen.generate_scenarios(3)
        
        model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
        pyomo_model = model.build_model()
        
        solver = OptimizationSolver()
        solution = solver.solve(pyomo_model)
        
        # Model should solve (possibly with high shortage)
        assert solution is not None
    
    def test_single_scenario(self):
        """Test model with single scenario (deterministic)."""
        network_config, model_params, scenario_params = get_default_config()
        gen = ScenarioGenerator(network_config, scenario_params)
        scenarios = gen.generate_scenarios(1)
        
        model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
        pyomo_model = model.build_model()
        
        assert pyomo_model is not None


class TestCVaR:
    """Test CVaR functionality."""
    
    def test_cvar_variables_exist(self):
        """Test that CVaR variables are created."""
        network_config, model_params, scenario_params = get_default_config()
        gen = ScenarioGenerator(network_config, scenario_params)
        scenarios = gen.generate_scenarios(5)
        
        model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
        pyomo_model = model.build_model()
        
        assert hasattr(pyomo_model, 'var')
        assert hasattr(pyomo_model, 'cvar_excess')
    
    def test_different_alpha_values(self):
        """Test model with different CVaR confidence levels."""
        network_config, model_params, scenario_params = get_default_config()
        
        for alpha in [0.90, 0.95, 0.99]:
            model_params.alpha_cvar = alpha
            gen = ScenarioGenerator(network_config, scenario_params)
            scenarios = gen.generate_scenarios(3)
            
            model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
            pyomo_model = model.build_model()
            
            assert pyomo_model is not None


class TestEquityModes:
    """Test equity constraint modes."""
    
    def test_equity_mode_1(self):
        """Test Mode 1: minimum service level."""
        network_config, model_params, scenario_params = get_default_config()
        model_params.equity_mode = 1
        model_params.beta_min_service = 0.8
        
        gen = ScenarioGenerator(network_config, scenario_params)
        scenarios = gen.generate_scenarios(3)
        
        model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
        pyomo_model = model.build_model()
        
        assert hasattr(pyomo_model, 'min_service_constraint')
    
    def test_equity_mode_2(self):
        """Test Mode 2: minimize inequity."""
        network_config, model_params, scenario_params = get_default_config()
        model_params.equity_mode = 2
        
        gen = ScenarioGenerator(network_config, scenario_params)
        scenarios = gen.generate_scenarios(3)
        
        model = WildfireSupplyNetworkModel(network_config, model_params, scenarios)
        pyomo_model = model.build_model()
        
        assert hasattr(pyomo_model, 'service_level')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
