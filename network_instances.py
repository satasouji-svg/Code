"""
Network instance generator for creating multiple test cases.

This module provides predefined network instances of varying sizes and characteristics
to demonstrate model scalability and trade-offs in publishable experiments.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from config import NetworkConfig


class NetworkInstanceGenerator:
    """Generator for creating network instances of different scales and characteristics."""
    
    @staticmethod
    def create_small_instance() -> NetworkConfig:
        """
        Create SMALL instance (baseline): 3 suppliers, 2 DCs, 4 demand nodes.
        
        Characteristics:
        - Moderate capacities (some slack but not excessive)
        - Balanced costs
        - Baseline for comparison
        """
        return NetworkConfig(
            suppliers=['S1', 'S2', 'S3'],
            distribution_centers=['DC1', 'DC2'],
            demand_nodes=['D1', 'D2', 'D3', 'D4'],
            
            arcs={
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
            },
            
            facilities={
                'S1': {'capacity': 2000.0, 'exposure': 0.15, 'preposition_cost': 2.0},
                'S2': {'capacity': 1800.0, 'exposure': 0.2, 'preposition_cost': 2.5},
                'S3': {'capacity': 1600.0, 'exposure': 0.3, 'preposition_cost': 3.0},
                'DC1': {'storage_capacity': 1500.0, 'exposure': 0.1, 'holding_cost': 1.0},
                'DC2': {'storage_capacity': 1500.0, 'exposure': 0.12, 'holding_cost': 1.2},
            },
            
            base_demand={
                'D1': 300.0,
                'D2': 350.0,
                'D3': 280.0,
                'D4': 320.0,
            }
        )
    
    @staticmethod
    def create_medium_instance() -> NetworkConfig:
        """
        Create MEDIUM instance: 5 suppliers, 3 DCs, 7 demand nodes.
        
        Characteristics:
        - More routing options
        - Demonstrates scalability
        - Total demand ~2400 units
        """
        return NetworkConfig(
            suppliers=['S1', 'S2', 'S3', 'S4', 'S5'],
            distribution_centers=['DC1', 'DC2', 'DC3'],
            demand_nodes=['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7'],
            
            arcs={
                # Supplier to DC arcs (5 suppliers × 3 DCs = 15 arcs)
                ('S1', 'DC1'): {'capacity': 900.0, 'cost': 5.0, 'exposure': 0.2},
                ('S1', 'DC2'): {'capacity': 700.0, 'cost': 7.0, 'exposure': 0.3},
                ('S1', 'DC3'): {'capacity': 800.0, 'cost': 6.5, 'exposure': 0.25},
                
                ('S2', 'DC1'): {'capacity': 850.0, 'cost': 6.0, 'exposure': 0.25},
                ('S2', 'DC2'): {'capacity': 900.0, 'cost': 5.5, 'exposure': 0.15},
                ('S2', 'DC3'): {'capacity': 750.0, 'cost': 6.8, 'exposure': 0.22},
                
                ('S3', 'DC1'): {'capacity': 650.0, 'cost': 8.0, 'exposure': 0.4},
                ('S3', 'DC2'): {'capacity': 800.0, 'cost': 6.5, 'exposure': 0.35},
                ('S3', 'DC3'): {'capacity': 700.0, 'cost': 7.2, 'exposure': 0.3},
                
                ('S4', 'DC1'): {'capacity': 750.0, 'cost': 6.8, 'exposure': 0.28},
                ('S4', 'DC2'): {'capacity': 680.0, 'cost': 7.5, 'exposure': 0.32},
                ('S4', 'DC3'): {'capacity': 820.0, 'cost': 6.0, 'exposure': 0.18},
                
                ('S5', 'DC1'): {'capacity': 700.0, 'cost': 7.2, 'exposure': 0.35},
                ('S5', 'DC2'): {'capacity': 750.0, 'cost': 6.8, 'exposure': 0.27},
                ('S5', 'DC3'): {'capacity': 880.0, 'cost': 5.8, 'exposure': 0.16},
                
                # DC to demand arcs (3 DCs × 7 demand nodes = 21 arcs)
                ('DC1', 'D1'): {'capacity': 400.0, 'cost': 3.0, 'exposure': 0.1},
                ('DC1', 'D2'): {'capacity': 380.0, 'cost': 3.5, 'exposure': 0.15},
                ('DC1', 'D3'): {'capacity': 350.0, 'cost': 4.0, 'exposure': 0.2},
                ('DC1', 'D4'): {'capacity': 320.0, 'cost': 4.5, 'exposure': 0.25},
                ('DC1', 'D5'): {'capacity': 360.0, 'cost': 3.8, 'exposure': 0.18},
                ('DC1', 'D6'): {'capacity': 340.0, 'cost': 4.2, 'exposure': 0.22},
                ('DC1', 'D7'): {'capacity': 330.0, 'cost': 4.3, 'exposure': 0.23},
                
                ('DC2', 'D1'): {'capacity': 380.0, 'cost': 4.0, 'exposure': 0.2},
                ('DC2', 'D2'): {'capacity': 420.0, 'cost': 3.5, 'exposure': 0.15},
                ('DC2', 'D3'): {'capacity': 400.0, 'cost': 3.0, 'exposure': 0.1},
                ('DC2', 'D4'): {'capacity': 360.0, 'cost': 4.2, 'exposure': 0.18},
                ('DC2', 'D5'): {'capacity': 390.0, 'cost': 3.6, 'exposure': 0.14},
                ('DC2', 'D6'): {'capacity': 370.0, 'cost': 3.9, 'exposure': 0.17},
                ('DC2', 'D7'): {'capacity': 350.0, 'cost': 4.1, 'exposure': 0.19},
                
                ('DC3', 'D1'): {'capacity': 360.0, 'cost': 4.5, 'exposure': 0.25},
                ('DC3', 'D2'): {'capacity': 390.0, 'cost': 4.0, 'exposure': 0.2},
                ('DC3', 'D3'): {'capacity': 410.0, 'cost': 3.2, 'exposure': 0.12},
                ('DC3', 'D4'): {'capacity': 380.0, 'cost': 3.8, 'exposure': 0.16},
                ('DC3', 'D5'): {'capacity': 420.0, 'cost': 3.4, 'exposure': 0.13},
                ('DC3', 'D6'): {'capacity': 400.0, 'cost': 3.7, 'exposure': 0.15},
                ('DC3', 'D7'): {'capacity': 370.0, 'cost': 4.0, 'exposure': 0.18},
            },
            
            facilities={
                'S1': {'capacity': 2400.0, 'exposure': 0.15, 'preposition_cost': 2.0},
                'S2': {'capacity': 2200.0, 'exposure': 0.2, 'preposition_cost': 2.5},
                'S3': {'capacity': 2000.0, 'exposure': 0.3, 'preposition_cost': 3.0},
                'S4': {'capacity': 2100.0, 'exposure': 0.25, 'preposition_cost': 2.7},
                'S5': {'capacity': 2300.0, 'exposure': 0.18, 'preposition_cost': 2.2},
                'DC1': {'storage_capacity': 1800.0, 'exposure': 0.1, 'holding_cost': 1.0},
                'DC2': {'storage_capacity': 1900.0, 'exposure': 0.12, 'holding_cost': 1.2},
                'DC3': {'storage_capacity': 2000.0, 'exposure': 0.08, 'holding_cost': 0.9},
            },
            
            base_demand={
                'D1': 320.0,
                'D2': 360.0,
                'D3': 340.0,
                'D4': 350.0,
                'D5': 330.0,
                'D6': 345.0,
                'D7': 355.0,
            }
        )
    
    @staticmethod
    def create_large_instance() -> NetworkConfig:
        """
        Create LARGE instance: 7 suppliers, 4 DCs, 10 demand nodes.
        
        Characteristics:
        - Demonstrates model scalability
        - Complex routing possibilities
        - Total demand ~3500 units
        """
        return NetworkConfig(
            suppliers=['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7'],
            distribution_centers=['DC1', 'DC2', 'DC3', 'DC4'],
            demand_nodes=['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10'],
            
            arcs={
                # Supplier to DC arcs (7 suppliers × 4 DCs = 28 arcs)
                **{(f'S{i}', f'DC{j}'): {
                    'capacity': 700.0 + (i * 30) + (j * 20),
                    'cost': 5.0 + (abs(i - j) * 0.5),
                    'exposure': 0.15 + (i * 0.03) + (j * 0.02)
                } for i in range(1, 8) for j in range(1, 5)},
                
                # DC to demand arcs (4 DCs × 10 demand nodes = 40 arcs)
                **{(f'DC{i}', f'D{j}'): {
                    'capacity': 300.0 + (i * 15) + (j * 10),
                    'cost': 3.0 + (abs(i - (j % 4)) * 0.4),
                    'exposure': 0.1 + (i * 0.02) + (j * 0.01)
                } for i in range(1, 5) for j in range(1, 11)},
            },
            
            facilities={
                **{f'S{i}': {
                    'capacity': 2200.0 + (i * 100),
                    'exposure': 0.15 + (i * 0.025),
                    'preposition_cost': 2.0 + (i * 0.15)
                } for i in range(1, 8)},
                **{f'DC{i}': {
                    'storage_capacity': 1800.0 + (i * 100),
                    'exposure': 0.08 + (i * 0.01),
                    'holding_cost': 0.9 + (i * 0.1)
                } for i in range(1, 5)},
            },
            
            base_demand={
                **{f'D{i}': 320.0 + (i * 15) for i in range(1, 11)}
            }
        )
    
    @staticmethod
    def create_stress_instance() -> NetworkConfig:
        """
        Create STRESS instance: Medium size but with tight capacities.
        
        Characteristics:
        - 5 suppliers, 3 DCs, 7 demand nodes
        - TIGHT capacities (75% of medium instance - reduced from 60% for feasibility)
        - Higher exposure rates
        - LOWER emergency costs to make it viable
        - HIGHER equity requirements (95% instead of 75%)
        - Designed to make emergency trigger and equity bind
        """
        return NetworkConfig(
            suppliers=['S1', 'S2', 'S3', 'S4', 'S5'],
            distribution_centers=['DC1', 'DC2', 'DC3'],
            demand_nodes=['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7'],
            
            arcs={
                # Supplier to DC arcs - 75% of medium capacity (increased from 60% for feasibility)
                ('S1', 'DC1'): {'capacity': 675.0, 'cost': 5.0, 'exposure': 0.3},
                ('S1', 'DC2'): {'capacity': 525.0, 'cost': 7.0, 'exposure': 0.4},
                ('S1', 'DC3'): {'capacity': 600.0, 'cost': 6.5, 'exposure': 0.35},
                
                ('S2', 'DC1'): {'capacity': 638.0, 'cost': 6.0, 'exposure': 0.35},
                ('S2', 'DC2'): {'capacity': 675.0, 'cost': 5.5, 'exposure': 0.25},
                ('S2', 'DC3'): {'capacity': 563.0, 'cost': 6.8, 'exposure': 0.32},
                
                ('S3', 'DC1'): {'capacity': 488.0, 'cost': 8.0, 'exposure': 0.5},
                ('S3', 'DC2'): {'capacity': 600.0, 'cost': 6.5, 'exposure': 0.45},
                ('S3', 'DC3'): {'capacity': 525.0, 'cost': 7.2, 'exposure': 0.4},
                
                ('S4', 'DC1'): {'capacity': 563.0, 'cost': 6.8, 'exposure': 0.38},
                ('S4', 'DC2'): {'capacity': 510.0, 'cost': 7.5, 'exposure': 0.42},
                ('S4', 'DC3'): {'capacity': 615.0, 'cost': 6.0, 'exposure': 0.28},
                
                ('S5', 'DC1'): {'capacity': 525.0, 'cost': 7.2, 'exposure': 0.45},
                ('S5', 'DC2'): {'capacity': 563.0, 'cost': 6.8, 'exposure': 0.37},
                ('S5', 'DC3'): {'capacity': 660.0, 'cost': 5.8, 'exposure': 0.26},
                
                # DC to demand arcs - 75% of medium capacity  
                ('DC1', 'D1'): {'capacity': 300.0, 'cost': 3.0, 'exposure': 0.15},
                ('DC1', 'D2'): {'capacity': 285.0, 'cost': 3.5, 'exposure': 0.20},
                ('DC1', 'D3'): {'capacity': 263.0, 'cost': 4.0, 'exposure': 0.25},
                ('DC1', 'D4'): {'capacity': 240.0, 'cost': 4.5, 'exposure': 0.30},
                ('DC1', 'D5'): {'capacity': 270.0, 'cost': 3.8, 'exposure': 0.23},
                ('DC1', 'D6'): {'capacity': 255.0, 'cost': 4.2, 'exposure': 0.27},
                ('DC1', 'D7'): {'capacity': 248.0, 'cost': 4.3, 'exposure': 0.28},
                
                ('DC2', 'D1'): {'capacity': 285.0, 'cost': 4.0, 'exposure': 0.25},
                ('DC2', 'D2'): {'capacity': 315.0, 'cost': 3.5, 'exposure': 0.20},
                ('DC2', 'D3'): {'capacity': 300.0, 'cost': 3.0, 'exposure': 0.15},
                ('DC2', 'D4'): {'capacity': 270.0, 'cost': 4.2, 'exposure': 0.23},
                ('DC2', 'D5'): {'capacity': 293.0, 'cost': 3.6, 'exposure': 0.19},
                ('DC2', 'D6'): {'capacity': 278.0, 'cost': 3.9, 'exposure': 0.22},
                ('DC2', 'D7'): {'capacity': 263.0, 'cost': 4.1, 'exposure': 0.24},
                
                ('DC3', 'D1'): {'capacity': 270.0, 'cost': 4.5, 'exposure': 0.30},
                ('DC3', 'D2'): {'capacity': 293.0, 'cost': 4.0, 'exposure': 0.25},
                ('DC3', 'D3'): {'capacity': 308.0, 'cost': 3.2, 'exposure': 0.17},
                ('DC3', 'D4'): {'capacity': 285.0, 'cost': 3.8, 'exposure': 0.21},
                ('DC3', 'D5'): {'capacity': 315.0, 'cost': 3.4, 'exposure': 0.18},
                ('DC3', 'D6'): {'capacity': 300.0, 'cost': 3.7, 'exposure': 0.20},
                ('DC3', 'D7'): {'capacity': 278.0, 'cost': 4.0, 'exposure': 0.23},
            },
            
            facilities={
                'S1': {'capacity': 1800.0, 'exposure': 0.25, 'preposition_cost': 2.0},
                'S2': {'capacity': 1650.0, 'exposure': 0.3, 'preposition_cost': 2.5},
                'S3': {'capacity': 1500.0, 'exposure': 0.4, 'preposition_cost': 3.0},
                'S4': {'capacity': 1575.0, 'exposure': 0.35, 'preposition_cost': 2.7},
                'S5': {'capacity': 1725.0, 'exposure': 0.28, 'preposition_cost': 2.2},
                'DC1': {'storage_capacity': 1350.0, 'exposure': 0.15, 'holding_cost': 1.0},
                'DC2': {'storage_capacity': 1425.0, 'exposure': 0.17, 'holding_cost': 1.2},
                'DC3': {'storage_capacity': 1500.0, 'exposure': 0.13, 'holding_cost': 0.9},
            },
            
            base_demand={
                'D1': 320.0,
                'D2': 360.0,
                'D3': 340.0,
                'D4': 350.0,
                'D5': 330.0,
                'D6': 345.0,
                'D7': 355.0,
            }
        )


def get_instance_by_name(name: str) -> NetworkConfig:
    """
    Get a network instance by name.
    
    Args:
        name: Instance name ('small', 'medium', 'large', 'stress', 'challenging')
        
    Returns:
        NetworkConfig for the specified instance
    """
    instances = {
        'small': NetworkInstanceGenerator.create_small_instance,
        'medium': NetworkInstanceGenerator.create_medium_instance,
        'large': NetworkInstanceGenerator.create_large_instance,
        'stress': NetworkInstanceGenerator.create_stress_instance,
        'challenging': NetworkInstanceGenerator.create_challenging_small_instance,
    }
    
    if name.lower() not in instances:
        raise ValueError(f"Unknown instance '{name}'. Choose from: {list(instances.keys())}")
    
    return instances[name.lower()]()


def get_all_instances() -> Dict[str, NetworkConfig]:
    """Get all available network instances as a dictionary."""
    return {
        'small': NetworkInstanceGenerator.create_small_instance(),
        'medium': NetworkInstanceGenerator.create_medium_instance(),
        'large': NetworkInstanceGenerator.create_large_instance(),
        'stress': NetworkInstanceGenerator.create_stress_instance(),
        'challenging': NetworkInstanceGenerator.create_challenging_small_instance(),
    }


class NetworkInstanceGenerator:
    """Generator for creating network instances of different scales and characteristics."""
    
    @staticmethod
    def create_challenging_small_instance() -> NetworkConfig:
        """
        Create CHALLENGING SMALL instance: Same topology as small (3-2-4) but with tighter constraints.
        
        Characteristics:
        - Arc capacities reduced by 35% (tight routing)
        - Higher demand variability (50% stdev instead of 30%)
        - Higher disruption exposure (+50%)
        - Higher minimum satisfaction requirement (85% instead of 75%)
        - Lower emergency cost ($15 instead of $20 to make it competitive)
        
        This creates a non-trivial problem where:
        - Emergency procurement sometimes activates
        - Equity constraints actually bind
        - Trade-offs between cost/risk/equity are real
        """
        return NetworkConfig(
            suppliers=['S1', 'S2', 'S3'],
            distribution_centers=['DC1', 'DC2'],
            demand_nodes=['D1', 'D2', 'D3', 'D4'],
            
            arcs={
                # Supplier to DC arcs (65% of original capacity)
                ('S1', 'DC1'): {'capacity': 650.0, 'cost': 5.0, 'exposure': 0.30},
                ('S1', 'DC2'): {'capacity': 520.0, 'cost': 7.0, 'exposure': 0.45},
                ('S2', 'DC1'): {'capacity': 585.0, 'cost': 6.0, 'exposure': 0.38},
                ('S2', 'DC2'): {'capacity': 650.0, 'cost': 5.5, 'exposure': 0.23},
                ('S3', 'DC1'): {'capacity': 455.0, 'cost': 8.0, 'exposure': 0.60},
                ('S3', 'DC2'): {'capacity': 553.0, 'cost': 6.5, 'exposure': 0.53},
                # DC to demand arcs (65% of original capacity)
                ('DC1', 'D1'): {'capacity': 325.0, 'cost': 3.0, 'exposure': 0.15},
                ('DC1', 'D2'): {'capacity': 293.0, 'cost': 3.5, 'exposure': 0.23},
                ('DC1', 'D3'): {'capacity': 260.0, 'cost': 4.0, 'exposure': 0.30},
                ('DC1', 'D4'): {'capacity': 228.0, 'cost': 4.5, 'exposure': 0.38},
                ('DC2', 'D1'): {'capacity': 293.0, 'cost': 4.0, 'exposure': 0.30},
                ('DC2', 'D2'): {'capacity': 325.0, 'cost': 3.5, 'exposure': 0.23},
                ('DC2', 'D3'): {'capacity': 312.0, 'cost': 3.0, 'exposure': 0.15},
                ('DC2', 'D4'): {'capacity': 260.0, 'cost': 4.2, 'exposure': 0.27},
            },
            
            facilities={
                'S1': {'capacity': 1300.0, 'exposure': 0.23, 'preposition_cost': 2.0},
                'S2': {'capacity': 1170.0, 'exposure': 0.30, 'preposition_cost': 2.5},
                'S3': {'capacity': 1040.0, 'exposure': 0.45, 'preposition_cost': 3.0},
                'DC1': {'storage_capacity': 975.0, 'exposure': 0.15, 'holding_cost': 1.0},
                'DC2': {'storage_capacity': 975.0, 'exposure': 0.18, 'holding_cost': 1.2},
            },
            
            base_demand={
                'D1': 300.0,
                'D2': 350.0,
                'D3': 280.0,
                'D4': 320.0,
            }
        )


def print_instance_summary(name: str, network: NetworkConfig):
    """Print a summary of a network instance."""
    print(f"\n{'='*60}")
    print(f"Network Instance: {name.upper()}")
    print(f"{'='*60}")
    print(f"Suppliers: {len(network.suppliers)}")
    print(f"Distribution Centers: {len(network.distribution_centers)}")
    print(f"Demand Nodes: {len(network.demand_nodes)}")
    print(f"Total Arcs: {len(network.arcs)}")
    print(f"Total Base Demand: {sum(network.base_demand.values()):.0f} units")
    print(f"Total Supplier Capacity: {sum(f['capacity'] for f in network.facilities.values() if 'capacity' in f):.0f} units")
    print(f"Total DC Storage: {sum(f['storage_capacity'] for f in network.facilities.values() if 'storage_capacity' in f):.0f} units")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Test all instances
    for name, network in get_all_instances().items():
        print_instance_summary(name, network)
