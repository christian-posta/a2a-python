#!/usr/bin/env python3
"""Test client for the Supply Chain Optimizer Agent."""

import asyncio
import json
from typing import Any, Dict
import httpx

from a2a.client import ClientFactory, ClientConfig
from a2a.types import TransportProtocol


async def test_supply_chain_optimizer():
    """Test the Supply Chain Optimizer Agent."""
    
    # Create client with proper configuration
    async with httpx.AsyncClient() as httpx_client:
        # Create client configuration
        config = ClientConfig(
            httpx_client=httpx_client,
            supported_transports=[TransportProtocol.jsonrpc],  # This becomes 'JSONRPC'
            streaming=False  # Disable streaming for Phase 1
        )
        
        # Create client factory
        factory = ClientFactory(config)
        
        # Create a minimal agent card for testing
        from a2a.client import minimal_agent_card
        test_card = minimal_agent_card(
            url="http://localhost:9999/",
            transports=["JSONRPC"]  # Use uppercase to match TransportProtocol.jsonrpc
        )
        
        # Create client
        client = factory.create(test_card)
        
        print("🔍 Testing Supply Chain Optimizer Agent...")
        print("=" * 60)
        
        # Test 1: Basic supply chain optimization
        print("\n📋 Test 1: Basic Supply Chain Optimization")
        print("-" * 40)
        
        try:
            # Use the correct A2A client method
            from a2a.types import Message, Role
            from a2a.client.helpers import create_text_message_object
            import uuid
            
            message = create_text_message_object(role=Role.user, content="optimize laptop supply chain")
            
            # Send message using the client
            async for event in client.send_message(message):
                print("✅ Success!")
                print(f"Response: {event}")
                break  # Just get the first response for now
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 2: Cost-focused optimization
        print("\n💰 Test 2: Cost-Focused Optimization")
        print("-" * 40)
        
        try:
            message = create_text_message_object(role=Role.user, content="analyze and optimize our hardware procurement process for cost and speed")
            
            async for event in client.send_message(message):
                print("✅ Success!")
                print(f"Response: {event}")
                break
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Inventory-focused request
        print("\n📦 Test 3: Inventory-Focused Request")
        print("-" * 40)
        
        try:
            message = create_text_message_object(role=Role.user, content="ensure we have adequate MacBook inventory for Q2 hiring targets")
            
            async for event in client.send_message(message):
                print("✅ Success!")
                print(f"Response: {event}")
                break
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 4: JSON request format
        print("\n🔧 Test 4: JSON Request Format")
        print("-" * 40)
        
        try:
            json_request = {
                "request_type": "supply_chain_optimization",
                "focus": "laptop_inventory",
                "constraints": ["budget", "timeline"],
                "priority": "high"
            }
            
            # Convert JSON to text for now
            message = create_text_message_object(role=Role.user, content=json.dumps(json_request))
            
            async for event in client.send_message(message):
                print("✅ Success!")
                print(f"Response: {event}")
                break
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 5: Agent capabilities
        print("\n🔍 Test 5: Agent Capabilities")
        print("-" * 40)
        
        try:
            # Get agent card from the actual server
            from a2a.client import A2ACardResolver
            
            resolver = A2ACardResolver(httpx_client, "http://localhost:9999")
            agent_card = await resolver.get_agent_card()
            
            print("✅ Agent Card Retrieved!")
            print(f"Name: {agent_card.name}")
            print(f"Description: {agent_card.description}")
            print(f"Skills: {len(agent_card.skills)}")
            
            for skill in agent_card.skills:
                print(f"  - {skill.name}: {skill.description}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 6: Market Analysis Integration
        print("\n🔗 Test 6: Market Analysis Integration")
        print("-" * 40)
        
        try:
            message = create_text_message_object(role=Role.user, content="perform market analysis for laptop supply chain optimization")
            
            async for event in client.send_message(message):
                print("✅ Success!")
                print(f"Response: {event}")
                break
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 7: Regular request without market analysis
        print("\n📋 Test 7: Regular Request (No Market Analysis)")
        print("-" * 40)
        
        try:
            message = create_text_message_object(role=Role.user, content="optimize laptop supply chain")
            
            async for event in client.send_message(message):
                print("✅ Success!")
                print(f"Response: {event}")
                break
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 Testing Complete!")


async def test_business_policy_validation():
    """Test business policy validation functionality."""
    
    print("\n🔒 Testing Business Policy Validation...")
    print("=" * 60)
    
    # Import the business policies module
    try:
        from business_policies import business_policies
        
        print("✅ Business Policies Module Loaded!")
        
        # Test policy summary
        policy_summary = business_policies.get_policy_summary()
        print(f"\n📊 Policy Summary:")
        print(f"  - Inventory Buffer: {policy_summary['inventory_management']['buffer_months']} months")
        print(f"  - Approval Threshold: ${policy_summary['financial_controls']['approval_threshold']:,}")
        print(f"  - Max Order Value: ${policy_summary['financial_controls']['max_order_value']:,}")
        print(f"  - Preferred Vendors: {', '.join(policy_summary['vendor_management']['preferred_vendors'])}")
        
        # Test validation
        print(f"\n🔍 Testing Policy Validation:")
        
        # Test 1: Valid order
        test_order = {"order_value": 25000, "vendor": "Apple", "product": "MacBook Pro", "quantity": 100}
        validation = business_policies.validate_request_against_policies(test_order)
        print(f"  - Valid Order ($25k, Apple, 100 MacBooks): {'✅ Valid' if validation['is_valid'] else '❌ Invalid'}")
        if validation['warnings']:
            print(f"    Warnings: {validation['warnings']}")
        
        # Test 2: High-value order requiring approval
        test_order = {"order_value": 75000, "vendor": "Dell", "product": "Dell XPS", "quantity": 150}
        validation = business_policies.validate_request_against_policies(test_order)
        print(f"  - High-Value Order ($75k, Dell, 150 XPS): {'✅ Valid' if validation['is_valid'] else '❌ Invalid'}")
        if validation['warnings']:
            print(f"    Warnings: {validation['warnings']}")
        
        # Test 3: Order exceeding max value
        test_order = {"order_value": 150000, "vendor": "HP", "product": "HP EliteBook", "quantity": 200}
        validation = business_policies.validate_request_against_policies(test_order)
        print(f"  - Order Exceeding Max Value ($150k, HP, 200 EliteBooks): {'✅ Valid' if validation['is_valid'] else '❌ Invalid'}")
        if validation['violations']:
            print(f"    Violations: {validation['violations']}")
        
        # Test 4: Non-preferred vendor
        test_order = {"order_value": 30000, "vendor": "ASUS", "product": "ASUS ZenBook", "quantity": 50}
        validation = business_policies.validate_request_against_policies(test_order)
        print(f"  - Non-Preferred Vendor ($30k, ASUS, 50 ZenBooks): {'✅ Valid' if validation['is_valid'] else '❌ Invalid'}")
        if validation['warnings']:
            print(f"    Warnings: {validation['warnings']}")
            
    except ImportError as e:
        print(f"❌ Error importing business policies: {e}")
    except Exception as e:
        print(f"❌ Error testing business policies: {e}")


async def main():
    """Main test function."""
    print("🚀 Supply Chain Optimizer Agent Test Suite")
    print("=" * 60)
    
    # Test the agent
    await test_supply_chain_optimizer()
    
    # Test business policies
    await test_business_policy_validation()


if __name__ == "__main__":
    asyncio.run(main())
