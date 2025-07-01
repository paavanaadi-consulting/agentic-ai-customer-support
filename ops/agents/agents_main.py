"""
Agents Service Main Entry Point
"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import agents
from agents.query_agent import QueryAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.response_agent import ResponseAgent
from agents.enhanced_query_agent import EnhancedQueryAgent

# Import core components
from src.geneticML.engines.evolution_engine import EvolutionEngine
from src.geneticML.evaluators.fitness_evaluator import FitnessEvaluator

# Import configuration
from config.env_settings import CONFIG

# Configure logging
logging.basicConfig(
    level=getattr(logging, CONFIG.get('log_level', 'INFO').upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global agent instances
agents = {}
evolution_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app"""
    global agents, evolution_engine
    
    logger.info("Starting Agents Service...")
    
    try:
        # Initialize agents
        agents['query'] = QueryAgent()
        agents['knowledge'] = KnowledgeAgent()
        agents['response'] = ResponseAgent()
        agents['enhanced_query'] = EnhancedQueryAgent()
        
        # Initialize evolution engine
        fitness_evaluator = FitnessEvaluator()
        evolution_engine = EvolutionEngine(fitness_evaluator)
        
        logger.info("All agents and evolution engine initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize agents service: {e}")
        raise
    finally:
        logger.info("Shutting down Agents Service...")
        # Cleanup if needed
        agents.clear()


# Create FastAPI app
app = FastAPI(
    title="Agentic AI Customer Support - Agents Service",
    description="Microservice for AI agents in customer support system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agents",
        "agents_loaded": len(agents),
        "evolution_engine_active": evolution_engine is not None
    }


@app.get("/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    return {
        "agents": {
            name: {
                "type": type(agent).__name__,
                "initialized": True
            }
            for name, agent in agents.items()
        },
        "evolution_engine": {
            "initialized": evolution_engine is not None
        }
    }


@app.post("/agents/query/process")
async def process_query(query_data: dict):
    """Process a query using the query agent"""
    try:
        if 'query' not in agents:
            raise HTTPException(status_code=503, detail="Query agent not available")
        
        result = await agents['query'].process_query(query_data)
        return {"result": result, "agent": "query"}
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/knowledge/search")
async def search_knowledge(search_data: dict):
    """Search knowledge using the knowledge agent"""
    try:
        if 'knowledge' not in agents:
            raise HTTPException(status_code=503, detail="Knowledge agent not available")
        
        result = await agents['knowledge'].search_knowledge(search_data)
        return {"result": result, "agent": "knowledge"}
    except Exception as e:
        logger.error(f"Error searching knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/response/generate")
async def generate_response(response_data: dict):
    """Generate response using the response agent"""
    try:
        if 'response' not in agents:
            raise HTTPException(status_code=503, detail="Response agent not available")
        
        result = await agents['response'].generate_response(response_data)
        return {"result": result, "agent": "response"}
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/agents/enhanced-query/process")
async def process_enhanced_query(query_data: dict):
    """Process query using the enhanced query agent"""
    try:
        if 'enhanced_query' not in agents:
            raise HTTPException(status_code=503, detail="Enhanced query agent not available")
        
        result = await agents['enhanced_query'].process_query(query_data)
        return {"result": result, "agent": "enhanced_query"}
    except Exception as e:
        logger.error(f"Error processing enhanced query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evolution/evaluate")
async def evaluate_fitness(evaluation_data: dict):
    """Evaluate fitness using the evolution engine"""
    try:
        if evolution_engine is None:
            raise HTTPException(status_code=503, detail="Evolution engine not available")
        
        result = await evolution_engine.evaluate_fitness(evaluation_data)
        return {"result": result, "engine": "evolution"}
    except Exception as e:
        logger.error(f"Error evaluating fitness: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evolution/evolve")
async def evolve_agents(evolution_data: dict):
    """Evolve agents using the evolution engine"""
    try:
        if evolution_engine is None:
            raise HTTPException(status_code=503, detail="Evolution engine not available")
        
        result = await evolution_engine.evolve(evolution_data)
        return {"result": result, "engine": "evolution"}
    except Exception as e:
        logger.error(f"Error evolving agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("AGENTS_SERVICE_PORT", 8005))
    host = os.getenv("AGENTS_SERVICE_HOST", "0.0.0.0")
    
    logger.info(f"Starting Agents Service on {host}:{port}")
    
    uvicorn.run(
        "agents_main:app",
        host=host,
        port=port,
        reload=False,
        access_log=True
    )
