"""
FastAPI Server for Healthcare Agentic AI
Exposes agentic reasoning capabilities via REST API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import torch
from typing import List

from agent import HealthcareAgenticAI
from models import AgenticRequest, AgenticResponse, FeedbackRequest
from config import AgentConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Healthcare Agentic AI",
    description="True Agentic AI for clinical concept extraction with autonomous reasoning",
    version="1.0.0"
)

# CORS middleware (open for local testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global agent instance
agent: HealthcareAgenticAI = None

@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    global agent
    logger.info("Initializing Healthcare Agentic AI...")
    
    # Load UMLS API key from config
    umls_key = AgentConfig.get_umls_api_key()
    
    agent = HealthcareAgenticAI(model_size="8B", umls_api_key=umls_key)
    logger.info("Healthcare Agentic AI ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global agent
    if agent:
        agent.cleanup()
        torch.cuda.empty_cache()
    logger.info("Healthcare Agentic AI shutdown complete")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent_ready": agent is not None,
        "agent_type": "ReACT (Reasoning + Acting) Pattern"
    }

@app.get("/info")
async def info():
    """Agent information and capabilities"""
    memory_stats = agent.tools['memory'].get_memory_stats() if agent else {}
    
    return {
        "name": "Healthcare Agentic AI",
        "description": "True agentic AI with autonomous decision-making for clinical concept extraction",
        "agentic_features": {
            "autonomous_decision_making": "Agent decides which tools to use based on confidence and goal",
            "reasoning_loops": "Multi-step ReACT pattern with observation cycles",
            "self_correction": "Detects and fixes its own errors",
            "learning": "Learns from feedback and uses few-shot examples from memory",
            "goal_optimization": "Adapts strategy based on accuracy/speed/coverage goals"
        },
        "tools": {
            "concept_extractor": "LLM-based clinical concept extraction",
            "umls_validator": "UMLS terminology validation and enrichment",
            "phenotyping": "Hierarchical concept clustering and expansion",
            "self_correction": "Error detection and correction",
            "memory": "Few-shot learning from past successes"
        },
        "memory_stats": memory_stats
    }

@app.post("/reason", response_model=AgenticResponse)
async def reason(request: AgenticRequest):
    """
    Agentic reasoning endpoint.
    Returns full reasoning chain showing the agent's thought process.
    """
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    if not request.clinical_text or len(request.clinical_text.strip()) == 0:
        raise HTTPException(status_code=400, detail="clinical_text cannot be empty")
    
    try:
        logger.info(
            f"Received agentic reasoning request. Goal: {request.goal}, "
            f"Text length: {len(request.clinical_text)} chars"
        )
        
        response = await agent.reason(request)
        
        # Store successful extraction in memory for learning
        if response.confidence > 0.7:
            agent.tools['memory'].store_success(
                request.clinical_text,
                response.extracted_concepts,
                request.main_note,
                {
                    'confidence': response.confidence,
                    'tools_used': response.tools_used,
                    'goal': request.goal.value
                }
            )
        
        return response
    
    except Exception as e:
        logger.error(f"Error during agentic reasoning: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reason-batch")
async def reason_batch(requests: List[AgenticRequest]):
    """
    Batch agentic reasoning with GPU memory management.
    """
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    results = []
    batch_size = AgentConfig.BATCH_SIZE
    
    logger.info(f"Starting batch agentic reasoning. Total requests: {len(requests)}")
    
    for i in range(0, len(requests), batch_size):
        batch = requests[i:i+batch_size]
        
        for request in batch:
            try:
                response = await agent.reason(request)
                results.append(response)
            except Exception as e:
                logger.error(f"Error processing request {i}: {str(e)}")
                results.append(AgenticResponse(
                    status="error",
                    record_id=request.record_id,
                    extracted_concepts=[],
                    confidence=0.0,
                    reasoning_chain=[],
                    tools_used=[],
                    self_corrected=False,
                    learned_from_memory=False,
                    total_reasoning_steps=0,
                    script_runtime=0.0,
                    model_used="",
                    goal=request.goal.value,
                    error=str(e)
                ))
        
        # Clear GPU between batches (project pattern)
        torch.cuda.empty_cache()
        import time
        time.sleep(AgentConfig.SLEEP_BETWEEN_BATCHES)
    
    logger.info(f"Batch processing complete. Results: {len(results)}")
    
    return {
        "status": "batch_complete",
        "total_processed": len(results),
        "results": results
    }

@app.post("/feedback")
async def provide_feedback(feedback: FeedbackRequest):
    """
    Provide feedback for agent learning.
    """
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        await agent.provide_feedback({
            'clinical_text': feedback.clinical_text,
            'predicted_concepts': feedback.predicted_concepts,
            'correct_concepts': feedback.correct_concepts,
            'user_notes': feedback.user_notes
        })
        
        return {
            "status": "success",
            "message": "Feedback received and stored in agent memory for learning"
        }
    
    except Exception as e:
        logger.error(f"Error storing feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)