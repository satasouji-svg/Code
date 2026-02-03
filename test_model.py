"""
Simple test script to validate the optimization model implementation.

This script runs a series of basic tests to ensure the model is working correctly.
"""

import sys
from config import get_default_config
from scenario_generator import generate_scenarios
from data_validator import validate_data
from optimization_model import TwoStageStochasticModel


def test_configuration():
    """Test configuration creation and validation."""
    print("Testing configuration...")
    config = get_default_config()
    config.validate()
    assert len(config.network.suppliers) > 0
    assert len(config.network.distribution_centers) > 0
    assert len(config.network.demand_nodes) > 0
    print("✅ Configuration test passed")


def test_scenario_generation():
    """Test scenario generation."""
    print("\nTesting scenario generation...")
    config = get_default_config()
    config.scenario.n_scenarios = 5
    scenarios = generate_scenarios(config)
    
    assert len(scenarios) == 5
    assert abs(sum(s.probability for s in scenarios) - 1.0) < 1e-6
    
    for scenario in scenarios:
        assert len(scenario.demand) == len(config.network.demand_nodes)
        assert all(v >= 0 for v in scenario.demand.values())
    
    print("✅ Scenario generation test passed")


def test_data_validation():
    """Test data validation."""
    print("\nTesting data validation...")
    config = get_default_config()
    config.scenario.n_scenarios = 5
    scenarios = generate_scenarios(config)
    
    result = validate_data(config, scenarios)
    assert result == True
    print("✅ Data validation test passed")


def test_model_building():
    """Test model building."""
    print("\nTesting model building...")
    config = get_default_config()
    config.scenario.n_scenarios = 3
    scenarios = generate_scenarios(config)
    
    model = TwoStageStochasticModel(config, scenarios)
    model.build_model()
    
    assert model.model is not None
    assert len(model.model.variables()) > 0
    assert len(model.model.constraints) > 0
    print("✅ Model building test passed")


def test_optimization():
    """Test full optimization pipeline."""
    print("\nTesting optimization...")
    config = get_default_config()
    config.scenario.n_scenarios = 3
    scenarios = generate_scenarios(config)
    
    model = TwoStageStochasticModel(config, scenarios)
    model.build_model()
    result = model.solve()
    
    assert result.status == "Optimal"
    assert result.objective_value > 0
    assert len(result.prepositioned_inventory) == len(config.network.distribution_centers)
    assert result.expected_cost > 0
    assert result.cvar_value >= result.expected_cost
    print("✅ Optimization test passed")


def test_different_configurations():
    """Test with different configurations."""
    print("\nTesting different configurations...")
    
    # Test 1: High CVaR weight
    config = get_default_config()
    config.scenario.n_scenarios = 3
    config.optimization.cvar_weight = 0.8
    config.optimization.expectation_weight = 0.2
    scenarios = generate_scenarios(config)
    model = TwoStageStochasticModel(config, scenarios)
    model.build_model()
    result = model.solve()
    assert result.status == "Optimal"
    print("  ✅ High CVaR weight test passed")
    
    # Test 2: High equity requirement
    config = get_default_config()
    config.scenario.n_scenarios = 3
    config.optimization.min_demand_satisfaction = 0.90
    scenarios = generate_scenarios(config)
    model = TwoStageStochasticModel(config, scenarios)
    model.build_model()
    result = model.solve()
    assert result.status == "Optimal"
    assert result.min_satisfaction_ratio >= 0.90 - 1e-6
    print("  ✅ High equity requirement test passed")
    
    print("✅ Different configurations test passed")


def run_all_tests():
    """Run all tests."""
    print("="*80)
    print("RUNNING TESTS")
    print("="*80)
    
    tests = [
        test_configuration,
        test_scenario_generation,
        test_data_validation,
        test_model_building,
        test_optimization,
        test_different_configurations,
    ]
    
    failed = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    if failed == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ {failed}/{len(tests)} TESTS FAILED")
    print("="*80)
    
    return failed


if __name__ == "__main__":
    failed = run_all_tests()
    sys.exit(failed)
