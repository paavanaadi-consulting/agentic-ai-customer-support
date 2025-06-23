#!/usr/bin/env python3
"""
Local Testing Script for A2A Module
Run this script to test A2A agents locally with MCP integration
"""
import asyncio
import os
import sys
import logging
import time
from typing import Dict, Any, List
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/a2a_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Import A2A components
from a2a_protocol.base_a2a_agent import A2AAgent, A2AMessage
from mcp.mcp_client import MCPClientManager


class TestQueryAgent(A2AAgent):
    """Test Query Agent for local testing"""
    
    def __init__(self, agent_id: str, mcp_config: Dict[str, Any] = None):
        super().__init__(agent_id, "query", port=8101, mcp_config=mcp_config)
        self.processed_queries = []
    
    async def process_customer_query(self, query: str, customer_id: str) -> Dict[str, Any]:
        """Process a customer query"""
        logger.info(f"Processing query from customer {customer_id}: {query}")
        
        try:
            # Use MCP to get customer context
            if "mcp_database" in self.mcp_manager.clients:
                customer_context = await self.call_mcp_tool(
                    "mcp_database", 
                    "get_customer_context", 
                    {"customer_id": customer_id}
                )
                logger.info(f"Customer context: {customer_context}")
            
            # Create query message
            query_data = {
                "query": query,
                "customer_id": customer_id,
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id
            }
            
            # Send to knowledge agent
            knowledge_message = A2AMessage(
                sender_id=self.agent_id,
                receiver_id="knowledge-agent-1",
                message_type="query_analysis",
                payload=query_data
            )
            
            await self.send_message(knowledge_message)
            self.processed_queries.append(query_data)
            
            return {"success": True, "query_id": f"q_{int(time.time())}"}
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {"success": False, "error": str(e)}


class TestKnowledgeAgent(A2AAgent):
    """Test Knowledge Agent for local testing"""
    
    def __init__(self, agent_id: str, mcp_config: Dict[str, Any] = None):
        super().__init__(agent_id, "knowledge", port=8102, mcp_config=mcp_config)
        self.analyzed_queries = []
    
    async def _handle_query_analysis(self, message: A2AMessage):
        """Handle query analysis request"""
        logger.info(f"Analyzing query: {message.payload}")
        
        try:
            query = message.payload.get("query")
            customer_id = message.payload.get("customer_id")
            
            # Use MCP to search knowledge base
            if "mcp_database" in self.mcp_manager.clients:
                knowledge_results = await self.call_mcp_tool(
                    "mcp_database",
                    "search_knowledge_base",
                    {"search_term": query, "limit": 3}
                )
                logger.info(f"Knowledge search results: {knowledge_results}")
            
            # Create analysis result
            analysis_data = {
                "original_query": query,
                "customer_id": customer_id,
                "intent": "password_reset",  # Mock intent detection
                "confidence": 0.95,
                "suggested_articles": [],
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to response agent
            response_message = A2AMessage(
                sender_id=self.agent_id,
                receiver_id="response-agent-1",
                message_type="generate_response",
                payload=analysis_data,
                request_id=message.request_id
            )
            
            await self.send_message(response_message)
            self.analyzed_queries.append(analysis_data)
            
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
    
    async def _process_message(self, message: A2AMessage):
        """Process incoming messages"""
        if message.message_type == "query_analysis":
            await self._handle_query_analysis(message)
        else:
            await super()._process_message(message)


class TestResponseAgent(A2AAgent):
    """Test Response Agent for local testing"""
    
    def __init__(self, agent_id: str, mcp_config: Dict[str, Any] = None):
        super().__init__(agent_id, "response", port=8103, mcp_config=mcp_config)
        self.generated_responses = []
    
    async def _handle_generate_response(self, message: A2AMessage):
        """Handle response generation request"""
        logger.info(f"Generating response for: {message.payload}")
        
        try:
            query = message.payload.get("original_query")
            customer_id = message.payload.get("customer_id")
            intent = message.payload.get("intent")
            
            # Generate mock response based on intent
            if intent == "password_reset":
                response_text = ("To reset your password, please visit our login page and click "
                               "'Forgot Password'. You'll receive an email with reset instructions.")
            else:
                response_text = "Thank you for your question. Our support team will assist you shortly."
            
            response_data = {
                "query": query,
                "customer_id": customer_id,
                "response": response_text,
                "confidence": 0.9,
                "timestamp": datetime.now().isoformat()
            }
            
            # Use MCP to save interaction
            if "mcp_database" in self.mcp_manager.clients:
                interaction_result = await self.call_mcp_tool(
                    "mcp_database",
                    "save_interaction",
                    {
                        "interaction_data": {
                            "query_id": f"q_{int(time.time())}",
                            "customer_id": customer_id,
                            "query_text": query,
                            "agent_response": response_text,
                            "created_at": datetime.now().isoformat()
                        }
                    }
                )
                logger.info(f"Interaction saved: {interaction_result}")
            
            # Send response back to query agent
            final_message = A2AMessage(
                sender_id=self.agent_id,
                receiver_id=message.sender_id,
                message_type="response_ready",
                payload=response_data,
                request_id=message.request_id
            )
            
            await self.send_message(final_message)
            self.generated_responses.append(response_data)
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
    
    async def _process_message(self, message: A2AMessage):
        """Process incoming messages"""
        if message.message_type == "generate_response":
            await self._handle_generate_response(message)
        else:
            await super()._process_message(message)


class A2ATestOrchestrator:
    """Orchestrates A2A testing"""
    
    def __init__(self):
        self.agents = {}
        self.mcp_config = {
            "servers": {
                "mcp_database": {"uri": "ws://localhost:8001"},
                "mcp_kafka": {"uri": "ws://localhost:8002"}
            }
        }
    
    async def setup_agents(self):
        """Setup test agents"""
        logger.info("Setting up A2A test agents...")
        
        try:
            # Create agents
            self.agents["query"] = TestQueryAgent("query-agent-1", self.mcp_config)
            self.agents["knowledge"] = TestKnowledgeAgent("knowledge-agent-1", self.mcp_config)
            self.agents["response"] = TestResponseAgent("response-agent-1", self.mcp_config)
            
            # Start agents
            for agent_type, agent in self.agents.items():
                await agent.start()
                logger.info(f"{agent_type} agent started on port {agent.port}")
            
            # Wait for agents to fully initialize
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error setting up agents: {e}")
            raise
    
    async def run_test_scenario(self, customer_id: str, query: str):
        """Run a complete test scenario"""
        logger.info(f"Running test scenario: {query}")
        
        try:
            # Send query to query agent
            query_agent = self.agents["query"]
            result = await query_agent.process_customer_query(query, customer_id)
            
            # Wait for processing
            await asyncio.sleep(3)
            
            # Check results
            logger.info("Test Results:")
            logger.info(f"Query Agent processed queries: {len(query_agent.processed_queries)}")
            logger.info(f"Knowledge Agent analyzed queries: {len(self.agents['knowledge'].analyzed_queries)}")
            logger.info(f"Response Agent generated responses: {len(self.agents['response'].generated_responses)}")
            
            return {
                "success": True,
                "processed_queries": len(query_agent.processed_queries),
                "analyzed_queries": len(self.agents['knowledge'].analyzed_queries),
                "generated_responses": len(self.agents['response'].generated_responses),
                "latest_response": (self.agents['response'].generated_responses[-1] 
                                  if self.agents['response'].generated_responses else None)
            }
            
        except Exception as e:
            logger.error(f"Error in test scenario: {e}")
            return {"success": False, "error": str(e)}
    
    async def shutdown(self):
        """Shutdown all agents"""
        logger.info("Shutting down A2A test agents...")
        
        for agent in self.agents.values():
            try:
                await agent.stop()
            except Exception as e:
                logger.error(f"Error stopping agent: {e}")


async def main():
    """Main testing function"""
    print("🚀 Starting A2A Module Local Testing")
    print("=" * 50)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('.env.local')
    
    orchestrator = A2ATestOrchestrator()
    
    try:
        # Setup agents
        await orchestrator.setup_agents()
        
        # Run test scenarios
        test_scenarios = [
            ("test_customer_12345", "How do I reset my password?"),
            ("test_customer_67890", "What are your support hours?"),
            ("test_customer_11111", "I can't access my account"),
        ]
        
        for i, (customer_id, query) in enumerate(test_scenarios, 1):
            print(f"\n📋 Test Scenario {i}: {query}")
            print("-" * 30)
            
            result = await orchestrator.run_test_scenario(customer_id, query)
            
            if result["success"]:
                print(f"✅ Test passed!")
                print(f"   Processed queries: {result['processed_queries']}")
                print(f"   Analyzed queries: {result['analyzed_queries']}")
                print(f"   Generated responses: {result['generated_responses']}")
                
                if result["latest_response"]:
                    print(f"   Latest response: {result['latest_response']['response'][:100]}...")
            else:
                print(f"❌ Test failed: {result['error']}")
            
            # Wait between scenarios
            await asyncio.sleep(2)
        
        print(f"\n🎉 A2A Testing Complete!")
        print("Check logs/a2a_test.log for detailed logs")
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        logger.error(f"Testing failed: {e}")
    
    finally:
        await orchestrator.shutdown()


if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    # Run the test
    asyncio.run(main())
