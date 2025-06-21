"""
Example showing how to use the A2A-enabled system
"""
import asyncio
from a2a_protocol.simplified_main import SimplifiedGeneticAISystem

async def main():
    """Example of using the simplified A2A system"""
    # Initialize the simplified system
    ai_system = SimplifiedGeneticAISystem()
    await ai_system.initialize()
    # Process a customer query - MUCH SIMPLER!
    query_data = {
        'query': 'I am having trouble logging into my account',
        'customer_id': 'CUST_12345',
        'context': {
            'previous_attempts': 3,
            'last_login': '2024-06-15'
        }
    }
    # Simple one-line processing!
    result = await ai_system.process_query(query_data)
    print("\U0001F389 A2A Result:")
    print(f"Success: {result.get('success')}")
    print(f"Response: {result.get('response_result', {}).get('response', 'No response')}")
    print(f"Agents Used: {result.get('total_agents_used', 0)}")
    # Get system status
    status = await ai_system.get_system_status()
    print(f"\n\U0001F4CA System Status: {status}")
    # Shutdown
    await ai_system.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
