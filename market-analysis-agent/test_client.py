#!/usr/bin/env python3
"""Test client for the Market Analysis Agent."""

import asyncio
import json
from typing import Any, Dict
import httpx

from a2a.client import ClientFactory, ClientConfig
from a2a.types import TransportProtocol


async def test_market_analysis_agent():
    """Test the Market Analysis Agent."""
    
    # Create client with proper configuration
    async with httpx.AsyncClient() as httpx_client:
        # Create client configuration
        config = ClientConfig(
            httpx_client=httpx_client,
            supported_transports=[TransportProtocol.jsonrpc],
            streaming=False
        )
        
        # Create client factory
        factory = ClientFactory(config)
        
        # Create a minimal agent card for testing
        from a2a.client import minimal_agent_card
        test_card = minimal_agent_card(
            url="http://localhost:9998/",
            transports=["JSONRPC"]
        )
        
        # Create client
        client = factory.create(test_card)
        
        print("🔍 Testing Market Analysis Agent...")
        print("=" * 60)
        
        # Test 1: Basic inventory demand analysis
        print("\n📊 Test 1: Inventory Demand Analysis")
        print("-" * 40)
        
        try:
            from a2a.types import Message, Role
            from a2a.client.helpers import create_text_message_object
            
            message = create_text_message_object(role=Role.user, content="analyze laptop demand and inventory for engineering, sales, marketing, and operations teams")
            
            async for event in client.send_message(message):
                print("✅ Success!")
                print(f"Response: {event}")
                break
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 2: Market trend forecasting
        print("\n📈 Test 2: Market Trend Forecasting")
        print("-" * 40)
        
        try:
            message = create_text_message_object(role=Role.user, content="forecast laptop market trends and pricing for the next 6 months")
            
            async for event in client.send_message(message):
                print("✅ Success!")
                print(f"Response: {event}")
                break
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Demand pattern modeling
        print("\n👥 Test 3: Demand Pattern Modeling")
        print("-" * 40)
        
        try:
            message = create_text_message_object(role=Role.user, content="model laptop demand patterns for engineering and sales teams over the next 6 months")
            
            async for event in client.send_message(message):
                print("✅ Success!")
                print(f"Response: {event}")
                break
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 4: Comprehensive analysis
        print("\n🔍 Test 4: Comprehensive Market Analysis")
        print("-" * 40)
        
        try:
            message = create_text_message_object(role=Role.user, content="provide a comprehensive market analysis including inventory, trends, and demand patterns")
            
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
            
            resolver = A2ACardResolver(httpx_client, "http://localhost:9998")
            agent_card = await resolver.get_agent_card()
            
            print("✅ Agent Card Retrieved!")
            print(f"Name: {agent_card.name}")
            print(f"Description: {agent_card.description}")
            print(f"Skills: {len(agent_card.skills)}")
            
            for skill in agent_card.skills:
                print(f"  - {skill.name}: {skill.description}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 Testing Complete!")
        return True























async def main():
    """Main test function."""
    print("🚀 Market Analysis Agent Test Suite")
    print("=" * 60)
    
    # Test the agent
    await test_market_analysis_agent()


if __name__ == "__main__":
    asyncio.run(main())
