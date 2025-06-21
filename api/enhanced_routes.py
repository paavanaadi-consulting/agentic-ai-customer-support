"""
Enhanced API routes with database integration
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

# Pydantic models for API
class QueryRequest(BaseModel):
    query: str
    customer_id: str
    context: Dict[str, Any] = {}
    priority: str = "medium"

class FeedbackRequest(BaseModel):
    query_id: str
    customer_id: str
    satisfaction_score: int
    feedback_text: Optional[str] = None

class TicketUpdateRequest(BaseModel):
    ticket_id: str
    status: Optional[str] = None
    priority: Optional[str] = None
    satisfaction_score: Optional[int] = None
    satisfaction_comment: Optional[str] = None

def create_enhanced_app() -> FastAPI:
    """Create enhanced FastAPI application with database integration"""
    
    app = FastAPI(
        title="Enhanced Genetic AI Customer Support",
        description="AI-powered customer support with genetic algorithm optimization and database integration",
        version="2.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger = logging.getLogger("EnhancedAPI")
    
    @app.get("/")
    async def root():
        return {"message": "Enhanced Agentic AI Customer Support System", "version": "2.0.0"}
    
    @app.get("/health")
    async def health_check():
        """Enhanced health check with database status"""
        try:
            ai_system = app.state.ai_system
            status = await ai_system.get_enhanced_system_status()
            
            return {
                "status": "healthy" if status.get('initialized') else "initializing",
                "database_connected": status.get('data_sources', {}).get('database', {}).get('connected', False),
                "agents_active": len([a for a in status.get('agents', {}).values() if a]),
                "version": "2.0.0"
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            raise HTTPException(status_code=503, detail="Service unhealthy")
    
    @app.post("/api/v2/query")
    async def process_enhanced_query(request: QueryRequest):
        """Process customer query with full database integration"""
        try:
            ai_system = app.state.ai_system
            
            query_data = {
                "query": request.query,
                "customer_id": request.customer_id,
                "context": request.context,
                "priority": request.priority
            }
            
            result = await ai_system.process_query(query_data)
            
            return {
                "query_id": result.get('query_id'),
                "ticket_id": result.get('ticket_id'),
                "response": result.get('final_response'),
                "confidence": result.get('confidence_score'),
                "sources": result.get('sources_used', []),
                "related_articles": result.get('related_articles', []),
                "processing_time_ms": result.get('total_processing_time'),
                "success": result.get('success', False)
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v2/customer/{customer_id}/dashboard")
    async def get_customer_dashboard(customer_id: str):
        """Get customer-specific dashboard"""
        try:
            ai_system = app.state.ai_system
            dashboard_data = await ai_system.get_customer_dashboard(customer_id)
            
            if not dashboard_data:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            return dashboard_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting customer dashboard: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v2/tickets/{ticket_id}")
    async def get_ticket_details(ticket_id: str):
        """Get detailed ticket information"""
        try:
            ai_system = app.state.ai_system
            db = ai_system.database_service.db
            
            # Get ticket details with responses
            ticket_query = """
            SELECT 
                st.*,
                c.name as category_name,
                a.name as agent_name,
                cust.first_name,
                cust.last_name,
                cust.email as customer_email
            FROM support_tickets st
            LEFT JOIN categories c ON st.category_id = c.id
            LEFT JOIN agents a ON st.assigned_agent_id = a.id
            LEFT JOIN customers cust ON st.customer_id = cust.customer_id
            WHERE st.ticket_id = %s
            """
            
            responses_query = """
            SELECT *
            FROM ticket_responses
            WHERE ticket_id = %s
            ORDER BY created_at ASC
            """
            
            with db.connection.cursor() as cursor:
                # Get ticket
                cursor.execute(ticket_query, (ticket_id,))
                ticket = cursor.fetchone()
                
                if not ticket:
                    raise HTTPException(status_code=404, detail="Ticket not found")
                
                # Get responses
                cursor.execute(responses_query, (ticket_id,))
                responses = cursor.fetchall()
                
                return {
                    "ticket": dict(ticket),
                    "responses": [dict(response) for response in responses]
                }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting ticket details: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.put("/api/v2/tickets/{ticket_id}")
    async def update_ticket(ticket_id: str, request: TicketUpdateRequest):
        """Update ticket information"""
        try:
            ai_system = app.state.ai_system
            db = ai_system.database_service.db
            
            updates = {}
            if request.status:
                updates['status'] = request.status
                if request.status == 'resolved':
                    updates['resolved_at'] = 'CURRENT_TIMESTAMP'
                elif request.status == 'closed':
                    updates['closed_at'] = 'CURRENT_TIMESTAMP'
            
            if request.priority:
                updates['priority'] = request.priority
            
            if request.satisfaction_score:
                updates['satisfaction_score'] = request.satisfaction_score
            
            if request.satisfaction_comment:
                updates['satisfaction_comment'] = request.satisfaction_comment
            
            success = await db.update_ticket(ticket_id, updates)
            
            if not success:
                raise HTTPException(status_code=404, detail="Ticket not found or update failed")
            
            return {"success": True, "message": "Ticket updated successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating ticket: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/v2/feedback")
    async def submit_feedback(request: FeedbackRequest):
        """Submit customer feedback"""
        try:
            ai_system = app.state.ai_system
            db = ai_system.database_service.db
            
            feedback_data = {
                'feedback_id': f"FB_{int(time.time())}",
                'customer_id': request.customer_id,
                'query_id': request.query_id,
                'feedback_type': 'satisfaction',
                'rating': request.satisfaction_score,
                'comment': request.feedback_text
            }
            
            # Save feedback
            feedback_query = """
            INSERT INTO customer_feedback 
            (feedback_id, customer_id, query_id, feedback_type, rating, comment)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            with db.connection.cursor() as cursor:
                cursor.execute(feedback_query, (
                    feedback_data['feedback_id'],
                    feedback_data['customer_id'],
                    feedback_data['query_id'],
                    feedback_data['feedback_type'],
                    feedback_data['rating'],
                    feedback_data['comment']
                ))
            
            # Update query interaction with satisfaction score
            update_query = """
            UPDATE query_interactions 
            SET customer_satisfaction = %s
            WHERE query_id = %s
            """
            
            with db.connection.cursor() as cursor:
                cursor.execute(update_query, (request.satisfaction_score, request.query_id))
            
            return {"success": True, "message": "Feedback submitted successfully"}
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v2/analytics/system")
    async def get_system_analytics():
        """Get system analytics and performance metrics"""
        try:
            ai_system = app.state.ai_system
            analytics = await ai_system.database_service.get_system_health()
            
            return {
                "analytics": analytics,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system analytics: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/v2/analytics/trending")
    async def get_trending_issues():
        """Get trending issues and patterns"""
        try:
            ai_system = app.state.ai_system
            db = ai_system.database_service.db
            
            trending = await db.get_trending_issues(days=7, limit=10)
            
            return {
                "trending_issues": trending,
                "period": "7 days"
            }
            
        except Exception as e:
            logger.error(f"Error getting trending issues: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app