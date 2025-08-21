"""
Business policies configuration for the Supply Chain Optimizer Agent.

This module contains the business rules, thresholds, and policies that the agent
applies when analyzing supply chain optimization requests.
"""

from typing import Dict, Any, List


class BusinessPolicies:
    """Business policies and rules for supply chain optimization."""
    
    def __init__(self):
        # Inventory management policies
        self.inventory_buffer_months = 3
        self.minimum_stock_levels = {
            "MacBook Pro": 50,
            "MacBook Air": 75,
            "Dell XPS": 40,
            "HP EliteBook": 60
        }
        
        # Financial approval policies
        self.approval_threshold = 50000  # $50k threshold for CFO approval
        self.max_order_value = 100000    # $100k max per order
        self.budget_allocations = {
            "Q1": 250000,
            "Q2": 300000,
            "Q3": 275000,
            "Q4": 325000
        }
        
        # Vendor management policies
        self.preferred_vendors = ["Apple", "Dell", "HP", "Lenovo"]
        self.approved_vendor_tiers = {
            "tier_1": ["Apple", "Dell"],      # Preferred, best pricing
            "tier_2": ["HP", "Lenovo"],       # Approved, competitive pricing
            "tier_3": ["Microsoft", "ASUS"]   # Conditional approval
        }
        
        # Product specifications
        self.target_laptop_types = [
            "MacBook Pro", "MacBook Air", "Dell XPS", "HP EliteBook"
        ]
        
        # Compliance requirements
        self.compliance_requirements = [
            "ISO 27001 certified vendors",
            "GDPR compliant data handling",
            "SOC 2 Type II compliance",
            "Vendor security assessments completed"
        ]
        
        # Operational constraints
        self.lead_time_requirements = {
            "standard_orders": "2-4 weeks",
            "rush_orders": "1-2 weeks",
            "bulk_orders": "6-8 weeks"
        }
        
        # Quality standards
        self.quality_standards = {
            "warranty_minimum": "3 years",
            "support_level": "24/7 enterprise support",
            "reliability_target": "99.5% uptime"
        }

    def get_policy_summary(self) -> Dict[str, Any]:
        """Get a summary of all business policies for display."""
        return {
            "inventory_management": {
                "buffer_months": self.inventory_buffer_months,
                "minimum_stock_levels": self.minimum_stock_levels
            },
            "financial_controls": {
                "approval_threshold": self.approval_threshold,
                "max_order_value": self.max_order_value,
                "quarterly_budgets": self.budget_allocations
            },
            "vendor_management": {
                "preferred_vendors": self.preferred_vendors,
                "vendor_tiers": self.approved_vendor_tiers
            },
            "compliance": {
                "requirements": self.compliance_requirements,
                "quality_standards": self.quality_standards
            },
            "operational": {
                "lead_times": self.lead_time_requirements,
                "target_products": self.target_laptop_types
            }
        }

    def validate_request_against_policies(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a request against current business policies."""
        validation_result = {
            "is_valid": True,
            "violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check order value against approval threshold
        if "order_value" in request_data:
            order_value = request_data["order_value"]
            if order_value > self.max_order_value:
                validation_result["is_valid"] = False
                validation_result["violations"].append(
                    f"Order value ${order_value:,} exceeds maximum allowed ${self.max_order_value:,}"
                )
            elif order_value > self.approval_threshold:
                validation_result["warnings"].append(
                    f"Order value ${order_value:,} requires CFO approval (threshold: ${self.approval_threshold:,})"
                )
        
        # Check vendor against approved list
        if "vendor" in request_data:
            vendor = request_data["vendor"]
            if vendor not in self.preferred_vendors:
                validation_result["warnings"].append(
                    f"Vendor '{vendor}' is not in preferred vendor list"
                )
        
        # Check inventory levels
        if "product" in request_data and "quantity" in request_data:
            product = request_data["product"]
            quantity = request_data["quantity"]
            if product in self.minimum_stock_levels:
                min_level = self.minimum_stock_levels[product]
                if quantity < min_level:
                    validation_result["warnings"].append(
                        f"Order quantity {quantity} for {product} is below minimum stock level {min_level}"
                    )
        
        return validation_result


# Global instance for easy access
business_policies = BusinessPolicies()
