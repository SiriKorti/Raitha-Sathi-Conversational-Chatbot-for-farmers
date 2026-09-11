"""
farm_economics.py — Basic Farm Cost Calculator

WHAT IT DOES:
A lightweight utility to calculate the estimated cost of pesticide 
or fertilizer application based on land area.

WHY IT EXISTS:
Allows the assistant to give rough estimates (e.g., "For 1 acre, 
you might need 500ml costing roughly ₹400").
"""

class FarmEconomics:
    @staticmethod
    def estimate_cost(area_acres: float, dosage_per_acre_ml: float, price_per_liter: float) -> float:
        """
        Estimate the cost of a pesticide/fertilizer application.
        
        Args:
            area_acres: Size of the farm in acres.
            dosage_per_acre_ml: How much chemical is needed per acre (in ml).
            price_per_liter: Approximate cost of the chemical per liter (in ₹).
            
        Returns:
            Estimated total cost in ₹.
        """
        total_ml_needed = area_acres * dosage_per_acre_ml
        total_liters = total_ml_needed / 1000.0
        return round(total_liters * price_per_liter, 2)

    @staticmethod
    def format_cost_estimate(cost: float, chemical_name: str) -> str:
        """Format the cost estimate nicely in Kannada."""
        return f"ಅಂದಾಜು ವೆಚ್ಚ ({chemical_name}): ₹{cost}"
