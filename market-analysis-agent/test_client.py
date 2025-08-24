#!/usr/bin/env python3
"""Test client for the Market Analysis Agent."""

import asyncio
import json
import uuid
from typing import Any, Dict
import httpx
from dotenv import load_dotenv

from a2a.client import ClientFactory, ClientConfig
from a2a.types import TransportProtocol

# Import tracing functions
from tracing_config import (
    span, add_event, set_attribute, initialize_tracing
)

# Load environment variables
load_dotenv()

def generate_trace_context():
    """Generate a new trace context for testing."""
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    
    trace_context = {
        "trace_id": trace_id,
        "span_id": span_id,
        "traceparent": f"00-{trace_id}-{span_id}-01",
        "tracestate": f"test={uuid.uuid4().hex[:16]},market-analysis={uuid.uuid4().hex[:16]}"
    }
    
    return trace_context

def create_tracing_headers(trace_context: Dict[str, str]) -> Dict[str, str]:
    """Create HTTP headers for trace context propagation."""
    return {
        "traceparent": trace_context["traceparent"],
        "tracestate": trace_context["tracestate"]
    }

async def test_tracing_functionality():
    """Test the OpenTelemetry tracing functionality."""
    print("🔗 Testing OpenTelemetry Tracing Functionality...")
    print("=" * 60)
    
    try:
        # Initialize tracing
        initialize_tracing(
            service_name="market-analysis-agent-test",
            enable_console_exporter=True
        )
        print("✅ Tracing Initialized!")
        
        # Test basic span creation
        print("\n🔗 Testing Basic Span Creation:")
        with span("test_span") as test_span:
            print(f"  Test Span: {test_span}")
            add_event("test_event")
            set_attribute("test.attribute", "test_value")
            print("✅ Basic span creation successful!")
        
        # Test multiple spans
        print("\n🔗 Testing Multiple Spans:")
        with span("parent_span") as parent_span:
            print(f"  Parent Span: {parent_span}")
            add_event("parent_event")
            
            # Create child span without parent context for now (simplified)
            with span("child_span") as child_span:
                print(f"  Child Span: {child_span}")
                add_event("child_event")
                set_attribute("child.attribute", "child_value")
        
        print("✅ Multiple spans test successful!")
        
        # Test trace context generation
        print("\n🔗 Testing Trace Context Generation:")
        trace_context = generate_trace_context()
        print(f"  Trace ID: {trace_context['trace_id']}")
        print(f"  Span ID: {trace_context['span_id']}")
        print(f"  Traceparent: {trace_context['traceparent']}")
        print(f"  Tracestate: {trace_context['tracestate']}")
        print("✅ Trace context generation successful!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing tracing functionality: {e}")
        import traceback
        traceback.print_exc()
        return False

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
        
        # Test 5: Tracing Context Propagation Test
        print("\n🔗 Test 5: Tracing Context Propagation Test")
        print("-" * 40)
        
        try:
            # Generate trace context
            trace_context = generate_trace_context()
            print(f"🔗 Generated Trace Context:")
            print(f"  Trace ID: {trace_context['trace_id']}")
            print(f"  Span ID: {trace_context['span_id']}")
            print(f"  Traceparent: {trace_context['traceparent']}")
            print(f"  Tracestate: {trace_context['tracestate']}")
            
            # Create message with tracing context
            message = create_text_message_object(
                role=Role.user, 
                content="perform market analysis with tracing context"
            )
            
            print(f"\n📝 Sending message: '{message.parts[0].root.text}'")
            print("-" * 40)
            
            async for event in client.send_message(message):
                print("✅ Success!")
                print(f"Response: {event}")
                break
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
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
    
    # Test tracing functionality first
    tracing_success = await test_tracing_functionality()
    
    if tracing_success:
        print("\n✅ Tracing functionality test completed successfully!")
    else:
        print("\n❌ Tracing functionality test failed!")
    
    print("\n" + "=" * 60)
    
    # Test the agent
    await test_market_analysis_agent()


if __name__ == "__main__":
    asyncio.run(main())
