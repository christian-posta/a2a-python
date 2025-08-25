from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
import json
import os
from typing import Dict, Any, List
from business_policies import business_policies
import httpx
from a2a.client import ClientFactory, ClientConfig
from a2a.types import TransportProtocol, Message, Role
from a2a.client.helpers import create_text_message_object
from a2a.client.middleware import ClientCallInterceptor, ClientCallContext
from tracing_config import (
    span, add_event, set_attribute, extract_context_from_headers, 
    inject_context_to_headers, initialize_tracing
)


class TracingInterceptor(ClientCallInterceptor):
    """Interceptor that injects trace context into HTTP requests."""
    
    def __init__(self, trace_headers: Dict[str, str]):
        self.trace_headers = trace_headers
    
    async def intercept(
        self,
        method_name: str,
        request_payload: dict[str, Any],
        http_kwargs: dict[str, Any],
        agent_card: Any | None,
        context: ClientCallContext | None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Inject trace headers into the HTTP request."""
        headers = http_kwargs.get('headers', {})
        headers.update(self.trace_headers)
        http_kwargs['headers'] = headers
        print(f"🔗 TracingInterceptor: Injected headers: {self.trace_headers}")
        return request_payload, http_kwargs


class SupplyChainOptimizerAgent:
    """Supply Chain Optimizer Agent that orchestrates laptop supply chain optimization."""

    def __init__(self):
        # Initialize tracing
        initialize_tracing(
            service_name="supply-chain-agent",
            jaeger_host=os.getenv("JAEGER_HOST"),
            jaeger_port=int(os.getenv("JAEGER_PORT", "4317")),
            enable_console_exporter=True
        )
        
        # Use business policies from configuration
        self.policies = business_policies
        # Market analysis agent client configuration
        self.market_analysis_url = os.getenv(
            "MARKET_ANALYSIS_AGENT_URL", 
            "http://localhost:9998/"
        )
        print(f"🔗 Market Analysis Agent URL: {self.market_analysis_url}")
        self.market_analysis_client = None

    async def _get_market_analysis_client(self):
        """Get or create the market analysis agent client."""
        if self.market_analysis_client is None:
            try:
                add_event("creating_market_analysis_client")
                set_attribute("market_analysis.url", self.market_analysis_url)
                
                # Create httpx client for the market analysis agent with extended timeout
                # Timeouts can be configured via environment variables
                connect_timeout = float(os.getenv("MARKET_ANALYSIS_CONNECT_TIMEOUT", "30.0"))
                read_timeout = float(os.getenv("MARKET_ANALYSIS_READ_TIMEOUT", "120.0"))
                write_timeout = float(os.getenv("MARKET_ANALYSIS_WRITE_TIMEOUT", "30.0"))
                pool_timeout = float(os.getenv("MARKET_ANALYSIS_POOL_TIMEOUT", "30.0"))
                
                httpx_client = httpx.AsyncClient(
                    timeout=httpx.Timeout(
                        connect=connect_timeout,      # Connection timeout
                        read=read_timeout,           # Read timeout (for long-running operations)
                        write=write_timeout,         # Write timeout
                        pool=pool_timeout            # Pool timeout
                    )
                )
                
                # Log the configured timeouts
                print(f"⏱️  Market Analysis Client Timeouts:")
                print(f"   Connect: {connect_timeout}s")
                print(f"   Read: {read_timeout}s")
                print(f"   Write: {write_timeout}s")
                print(f"   Pool: {pool_timeout}s")
                
                # Create client configuration
                config = ClientConfig(
                    httpx_client=httpx_client,
                    supported_transports=[TransportProtocol.jsonrpc],
                    streaming=False
                )
                
                # Create client factory
                factory = ClientFactory(config)
                
                # Create minimal agent card for market analysis agent
                from a2a.client import minimal_agent_card
                market_analysis_card = minimal_agent_card(
                    url=self.market_analysis_url,
                    transports=["JSONRPC"]
                )
                
                # Create client
                self.market_analysis_client = factory.create(market_analysis_card)
                add_event("market_analysis_client_created")
                set_attribute("market_analysis.client_ready", True)
                
            except Exception as e:
                add_event("market_analysis_client_creation_failed", {"error": str(e)})
                set_attribute("market_analysis.client_error", str(e))
                print(f"Warning: Could not create market analysis client: {e}")
                self.market_analysis_client = None
        
        return self.market_analysis_client

    async def _get_market_analysis(self, request_text: str, trace_context: Any) -> str:
        """Get market analysis from the market analysis agent."""
        with span("supply_chain_agent.get_market_analysis", {
            "request.text": request_text[:100],  # Truncate for attribute limits
            "market_analysis.requested": True
        }, parent_context=trace_context) as span_obj:
            
            try:
                add_event("market_analysis_requested", {"request_text": request_text})
                
                print(f"🔄 Getting market analysis client...")
                client = await self._get_market_analysis_client()
                if client is None:
                    add_event("market_analysis_client_unavailable")
                    set_attribute("market_analysis.client_available", False)
                    print(f"❌ No market analysis client available")
                    return "No market analysis provided"
                
                add_event("market_analysis_client_ready")
                set_attribute("market_analysis.client_available", True)
                print(f"✅ Market analysis client ready")
                
                # Create message for market analysis
                message = create_text_message_object(
                    role=Role.user, 
                    content=f"Please provide market analysis for: {request_text}"
                )
                
                add_event("market_analysis_message_created", {"message_content": str(message)[:100]})
                print(f"📤 Sending message to market analysis agent: {message}")
                
                # Get response from market analysis agent
                market_response = ""
                async for event in client.send_message(message):
                    add_event("market_analysis_response_received", {"event_type": str(type(event))})
                    print(f"📥 Received event: {type(event)}")
                    if hasattr(event, 'content') and event.content:
                        if isinstance(event.content, str):
                            market_response += event.content
                            print(f"📝 String content: {event.content[:50]}...")
                        elif isinstance(event.content, dict) and 'content' in event.content:
                            market_response += event.content['content']
                            print(f"📝 Dict content: {event.content['content'][:50]}...")
                    elif hasattr(event, 'text'):
                        market_response += event.text
                        print(f"📝 Text attribute: {event.text[:50]}...")
                    elif hasattr(event, 'parts') and event.parts:
                        # Handle parts structure
                        for part in event.parts:
                            if hasattr(part, 'root') and hasattr(part.root, 'text'):
                                market_response += part.root.text
                                print(f"📝 Part text: {part.root.text[:50]}...")
                    
                    # Just get the first response for now
                    break
                
                add_event("market_analysis_completed", {"response_length": len(market_response)})
                set_attribute("market_analysis.response_length", len(market_response))
                print(f"📊 Final market response: {market_response[:100]}...")
                return market_response if market_response else "No market analysis provided"
                
            except Exception as e:
                add_event("market_analysis_error", {"error": str(e)})
                set_attribute("market_analysis.error", str(e))
                print(f"❌ Error getting market analysis: {e}")
                import traceback
                traceback.print_exc()
                return "No market analysis provided"

    async def invoke(self, request_text: str = "", trace_context: Any = None) -> str:
        """Main entry point for supply chain optimization requests."""
        with span("supply_chain_agent.invoke", {
            "request.text": request_text[:100],
            "request.has_content": bool(request_text)
        }, parent_context=trace_context) as span_obj:
            
            if not request_text:
                request_text = "optimize laptop supply chain"
                add_event("using_default_request")
            
            add_event("invoke_started", {"request_text": request_text})
            
            # Parse the request and apply business logic
            analysis = self._analyze_request(request_text)
            add_event("request_analysis_completed", {"analysis_keys": list(analysis.keys())})
            
            recommendations = self._generate_recommendations(analysis)
            add_event("recommendations_generated", {"recommendations_count": len(recommendations)})
            
            # Check if market analysis is requested
            market_analysis = ""
            if "perform market analysis" in request_text.lower():
                add_event("market_analysis_requested")
                set_attribute("market_analysis.requested", True)
                print(f"🔍 Market analysis requested for: {request_text}")
                market_analysis = await self._get_market_analysis(request_text, trace_context)
                print(f"📊 Market analysis result: {market_analysis[:100]}...")
            else:
                add_event("market_analysis_not_requested")
                set_attribute("market_analysis.requested", False)
                print(f"📋 No market analysis requested for: {request_text}")
            
            response = self._format_response(analysis, recommendations, market_analysis)
            add_event("response_formatted", {"response_length": len(response)})
            set_attribute("response.length", len(response))
            
            return response

    def _analyze_request(self, request: str) -> Dict[str, Any]:
        """Analyze the optimization request and apply business policies."""
        request_lower = request.lower()
        
        analysis = {
            "request_type": "supply_chain_optimization",
            "business_context": "IT hardware procurement",
            "current_policies": self.policies.get_policy_summary(),
            "analysis_timestamp": "2024-01-15T10:00:00Z"
        }
        
        add_event("analysis_started", {"request_type": analysis["request_type"]})
        
        # Determine optimization focus based on request
        if "laptop" in request_lower or "hardware" in request_lower:
            analysis["focus_area"] = "laptop_inventory"
            analysis["target_products"] = self.policies.target_laptop_types
            add_event("focus_area_determined", {"focus": "laptop_inventory"})
            set_attribute("analysis.focus_area", "laptop_inventory")
        
        if "cost" in request_lower or "budget" in request_lower:
            analysis["optimization_goal"] = "cost_optimization"
            analysis["budget_constraints"] = {
                "max_order": self.policies.max_order_value,
                "approval_threshold": self.policies.approval_threshold
            }
            add_event("optimization_goal_determined", {"goal": "cost_optimization"})
            set_attribute("analysis.optimization_goal", "cost_optimization")
        
        if "inventory" in request_lower or "stock" in request_lower:
            analysis["inventory_management"] = {
                "buffer_months": self.policies.inventory_buffer_months,
                "strategy": "maintain_adequate_buffer"
            }
            add_event("inventory_management_determined", {"buffer_months": self.policies.inventory_buffer_months})
            set_attribute("analysis.inventory_management.buffer_months", self.policies.inventory_buffer_months)
        
        add_event("analysis_completed", {"analysis_keys": list(analysis.keys())})
        return analysis

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []
        
        # Inventory optimization recommendation
        if "inventory_management" in analysis:
            recommendations.append({
                "type": "inventory_optimization",
                "priority": "high",
                "description": f"Maintain {analysis['inventory_management']['buffer_months']}-month inventory buffer for all laptop models",
                "action": "review_current_stock_levels_and_forecast_demand",
                "estimated_impact": "reduce_stockouts_by_80%"
            })
            add_event("inventory_recommendation_generated")
        
        # Cost optimization recommendation
        if "optimization_goal" == "cost_optimization":
            recommendations.append({
                "type": "cost_optimization",
                "priority": "medium",
                "description": "Consolidate orders to leverage volume discounts",
                "action": "batch_orders_quarterly_and_negotiate_bulk_pricing",
                "estimated_impact": "reduce_costs_by_15-20%"
            })
            add_event("cost_optimization_recommendation_generated")
        
        # Vendor management recommendation
        recommendations.append({
            "type": "vendor_management",
            "priority": "medium",
            "description": "Focus procurement on approved vendor list",
            "action": "prioritize_orders_with_approved_vendors",
            "estimated_impact": "ensure_compliance_and_quality"
        })
        add_event("vendor_management_recommendation_generated")
        
        # Approval workflow recommendation
        recommendations.append({
            "type": "approval_workflow",
            "priority": "low",
            "description": f"Orders above ${self.policies.approval_threshold:,} require CFO approval",
            "action": "implement_automated_approval_routing",
            "estimated_impact": "streamline_procurement_process"
        })
        add_event("approval_workflow_recommendation_generated")
        
        set_attribute("recommendations.count", len(recommendations))
        add_event("recommendations_generation_completed", {"count": len(recommendations)})
        return recommendations

    def _format_response(self, analysis: Dict[str, Any], recommendations: List[Dict[str, Any]], market_analysis: str = "") -> str:
        """Format the analysis and recommendations into a readable response."""
        response = f"""# Supply Chain Optimization Analysis

## Request Analysis
- **Type**: {analysis['request_type']}
- **Context**: {analysis['business_context']}
- **Focus Area**: {analysis.get('focus_area', 'general_supply_chain')}

## Business Policies Applied
- Inventory Buffer: {self.policies.inventory_buffer_months} months
- Approval Threshold: ${self.policies.approval_threshold:,}
- Max Order Value: ${self.policies.max_order_value:,}
- Preferred Vendors: {', '.join(self.policies.preferred_vendors)}

## Optimization Recommendations

"""
        
        for i, rec in enumerate(recommendations, 1):
            response += f"""### {i}. {rec['type'].replace('_', ' ').title()}
**Priority**: {rec['priority'].title()}
**Description**: {rec['description']}
**Action**: {rec['action']}
**Expected Impact**: {rec['estimated_impact']}

"""
        
        # Add market analysis section if available
        if market_analysis and market_analysis != "No market analysis provided":
            response += f"""## Market Analysis

{market_analysis}

"""
            add_event("market_analysis_included_in_response")
        
        response += """
## Next Steps
This analysis provides the foundation for supply chain optimization. For detailed implementation, consider delegating to specialized agents for:
- Market analysis and demand forecasting
- Vendor performance evaluation
- Procurement execution and order management

*Generated by Supply Chain Optimizer Agent v1.0*"""
        
        add_event("response_formatting_completed", {"response_length": len(response)})
        return response


class SupplyChainOptimizerExecutor(AgentExecutor):
    """Supply Chain Optimizer Agent Executor."""

    def __init__(self):
        self.agent = SupplyChainOptimizerAgent()

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        # Extract trace context from headers if available
        trace_context = None
        if hasattr(context, 'headers'):
            headers = context.headers
            trace_context = extract_context_from_headers(headers)
            if trace_context:
                add_event("trace_context_extracted_from_headers")
                set_attribute("tracing.context_extracted", True)
        
        # Create span with or without parent context
        if trace_context:
            # Case 1: With tracing headers - create child span
            with span("supply_chain_agent.executor.execute", parent_context=trace_context) as span_obj:
                await self._execute_with_tracing(context, event_queue, span_obj)
        else:
            # Case 2: No tracing headers - create root span
            with span("supply_chain_agent.executor.execute") as span_obj:
                add_event("no_trace_context_provided")
                set_attribute("tracing.context_extracted", False)
                await self._execute_with_tracing(context, event_queue, span_obj)
    
    async def _execute_with_tracing(
        self,
        context: RequestContext,
        event_queue: EventQueue,
        span_obj
    ):
        """Execute the agent logic with tracing support."""
        # Extract request text from context if available
        request_text = ""
        print(f"🔍 Executor: Context type: {type(context)}")
        print(f"🔍 Executor: Context attributes: {dir(context)}")
        
        # Method 1: Try to get from message attribute
        if hasattr(context, 'message') and context.message:
            print(f"🔍 Executor: Found message: {context.message}")
            if hasattr(context.message, 'parts') and context.message.parts:
                for part in context.message.parts:
                    if hasattr(part, 'root') and hasattr(part.root, 'text'):
                        request_text = part.root.text
                        print(f"🔍 Executor: Found text in message parts: {request_text}")
                        break
        
        # Method 2: Try to get from current_task.user_input
        if not request_text and hasattr(context, 'current_task') and context.current_task:
            print(f"🔍 Executor: Found current_task: {context.current_task}")
            if hasattr(context.current_task, 'user_input') and context.current_task.user_input:
                user_input = context.current_task.user_input
                print(f"🔍 Executor: User input from current_task: {user_input}")
                if isinstance(user_input, str):
                    request_text = user_input
                elif isinstance(user_input, list) and len(user_input) > 0:
                    request_text = user_input[0]
        
        # Method 3: Try to get from get_user_input method
        if not request_text and hasattr(context, 'get_user_input'):
            try:
                user_input = context.get_user_input()
                print(f"🔍 Executor: get_user_input result: {user_input}")
                if user_input:
                    if isinstance(user_input, str):
                        request_text = user_input
                    elif isinstance(user_input, list) and len(user_input) > 0:
                        request_text = user_input[0]
            except Exception as e:
                print(f"🔍 Executor: Error calling get_user_input: {e}")
                add_event("get_user_input_error", {"error": str(e)})
        
        # Method 4: Try to get from configuration or params
        if not request_text and hasattr(context, 'configuration'):
            config = context.configuration
            print(f"🔍 Executor: Configuration: {config}")
            if hasattr(config, 'user_input'):
                request_text = config.user_input
                print(f"🔍 Executor: User input from config: {request_text}")
        
        if not request_text:
            print(f"🔍 Executor: No request found in context, using default")
            request_text = "optimize laptop supply chain"  # Default fallback
            add_event("using_default_request")
        
        set_attribute("executor.request_text", request_text)
        add_event("executor_request_extracted", {"request_text": request_text})
        print(f"🔍 Executor: Final request_text: '{request_text}'")
        
        result = await self.agent.invoke(request_text)
        add_event("agent_invoke_completed", {"result_length": len(result)})
        
        await event_queue.enqueue_event(new_agent_text_message(result))
        add_event("response_enqueued")

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        with span("supply_chain_agent.executor.cancel") as span_obj:
            add_event("cancel_requested")
            raise Exception('cancel not supported')
