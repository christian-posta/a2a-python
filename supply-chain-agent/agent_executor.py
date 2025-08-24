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


class SupplyChainOptimizerAgent:
    """Supply Chain Optimizer Agent that orchestrates laptop supply chain optimization."""

    def __init__(self):
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
                # Create httpx client for the market analysis agent
                httpx_client = httpx.AsyncClient()
                
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
                
            except Exception as e:
                print(f"Warning: Could not create market analysis client: {e}")
                self.market_analysis_client = None
        
        return self.market_analysis_client

    async def _get_market_analysis(self, request_text: str) -> str:
        """Get market analysis from the market analysis agent."""
        try:
            print(f"🔄 Getting market analysis client...")
            client = await self._get_market_analysis_client()
            if client is None:
                print(f"❌ No market analysis client available")
                return "No market analysis provided"
            
            print(f"✅ Market analysis client ready")
            
            # Create message for market analysis
            message = create_text_message_object(
                role=Role.user, 
                content=f"Please provide market analysis for: {request_text}"
            )
            
            print(f"📤 Sending message to market analysis agent: {message}")
            
            # Get response from market analysis agent
            market_response = ""
            async for event in client.send_message(message):
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
            
            print(f"📊 Final market response: {market_response[:100]}...")
            return market_response if market_response else "No market analysis provided"
            
        except Exception as e:
            print(f"❌ Error getting market analysis: {e}")
            import traceback
            traceback.print_exc()
            return "No market analysis provided"

    async def invoke(self, request_text: str = "") -> str:
        """Main entry point for supply chain optimization requests."""
        if not request_text:
            request_text = "optimize laptop supply chain"
        
        # Parse the request and apply business logic
        analysis = self._analyze_request(request_text)
        recommendations = self._generate_recommendations(analysis)
        
        # Check if market analysis is requested
        market_analysis = ""
        if "perform market analysis" in request_text.lower():
            print(f"🔍 Market analysis requested for: {request_text}")
            market_analysis = await self._get_market_analysis(request_text)
            print(f"📊 Market analysis result: {market_analysis[:100]}...")
        else:
            print(f"📋 No market analysis requested for: {request_text}")
        
        return self._format_response(analysis, recommendations, market_analysis)

    def _analyze_request(self, request: str) -> Dict[str, Any]:
        """Analyze the optimization request and apply business policies."""
        request_lower = request.lower()
        
        analysis = {
            "request_type": "supply_chain_optimization",
            "business_context": "IT hardware procurement",
            "current_policies": self.policies.get_policy_summary(),
            "analysis_timestamp": "2024-01-15T10:00:00Z"
        }
        
        # Determine optimization focus based on request
        if "laptop" in request_lower or "hardware" in request_lower:
            analysis["focus_area"] = "laptop_inventory"
            analysis["target_products"] = self.policies.target_laptop_types
        
        if "cost" in request_lower or "budget" in request_lower:
            analysis["optimization_goal"] = "cost_optimization"
            analysis["budget_constraints"] = {
                "max_order": self.policies.max_order_value,
                "approval_threshold": self.policies.approval_threshold
            }
        
        if "inventory" in request_lower or "stock" in request_lower:
            analysis["inventory_management"] = {
                "buffer_months": self.policies.inventory_buffer_months,
                "strategy": "maintain_adequate_buffer"
            }
        
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
        
        # Cost optimization recommendation
        if "optimization_goal" == "cost_optimization":
            recommendations.append({
                "type": "cost_optimization",
                "priority": "medium",
                "description": "Consolidate orders to leverage volume discounts",
                "action": "batch_orders_quarterly_and_negotiate_bulk_pricing",
                "estimated_impact": "reduce_costs_by_15-20%"
            })
        
        # Vendor management recommendation
        recommendations.append({
            "type": "vendor_management",
            "priority": "medium",
            "description": "Focus procurement on approved vendor list",
            "action": "prioritize_orders_with_approved_vendors",
            "estimated_impact": "ensure_compliance_and_quality"
        })
        
        # Approval workflow recommendation
        recommendations.append({
            "type": "approval_workflow",
            "priority": "low",
            "description": f"Orders above ${self.policies.approval_threshold:,} require CFO approval",
            "action": "implement_automated_approval_routing",
            "estimated_impact": "streamline_procurement_process"
        })
        
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
        
        response += """
## Next Steps
This analysis provides the foundation for supply chain optimization. For detailed implementation, consider delegating to specialized agents for:
- Market analysis and demand forecasting
- Vendor performance evaluation
- Procurement execution and order management

*Generated by Supply Chain Optimizer Agent v1.0*"""
        
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
        
        print(f"🔍 Executor: Final request_text: '{request_text}'")
        
        result = await self.agent.invoke(request_text)
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise Exception('cancel not supported')
