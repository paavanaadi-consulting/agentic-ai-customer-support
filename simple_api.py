"""
Simple API main application
Direct PostgreSQL connection without MCP for testing
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncpg
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global database pool
db_pool = None

# Pydantic models
class CustomerCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class Customer(BaseModel):
    customer_id: str
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    created_at: datetime
    status: str = "active"
    tier: str = "standard"

class TicketCreate(BaseModel):
    title: str
    description: str
    customer_id: str
    priority: str = "medium"
    category: Optional[str] = "general"

class Ticket(BaseModel):
    ticket_id: str
    customer_id: str
    subject: str
    description: str
    status: str
    priority: str
    created_at: datetime

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global db_pool
    
    # Startup - Initialize database connection
    logger.info("Starting simple API server...")
    try:
        db_host = os.getenv('DB_HOST', 'postgres')
        db_port = int(os.getenv('DB_PORT', '5432'))
        db_name = os.getenv('DB_NAME', 'customer_support')
        db_user = os.getenv('DB_USER', 'admin')
        db_password = os.getenv('DB_PASSWORD', 'password')
        
        dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        db_pool = await asyncpg.create_pool(
            dsn,
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        
        logger.info("✅ Database connection pool initialized")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        yield
    finally:
        # Shutdown
        if db_pool:
            await db_pool.close()
            logger.info("Database connection pool closed")

# Create FastAPI app
app = FastAPI(
    title="Simple Customer Support API",
    description="Direct PostgreSQL API for testing",
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
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            db_status = "connected"
        else:
            db_status = "disconnected"
            
        return {
            "status": "healthy",
            "timestamp": datetime.now().timestamp(),
            "database": db_status,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().timestamp()
            }
        )

@app.get("/api/v1/customers", response_model=List[Customer])
async def get_customers(limit: int = 50, offset: int = 0):
    """Get list of customers"""
    try:
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not available")
            
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT customer_id, first_name, last_name, email, phone, 
                       company, created_at, is_active, tier
                FROM customers 
                ORDER BY created_at DESC 
                LIMIT $1 OFFSET $2
            """, limit, offset)
            
            customers = []
            for row in rows:
                customers.append(Customer(
                    customer_id=row['customer_id'],
                    name=f"{row['first_name']} {row['last_name']}",
                    email=row['email'],
                    phone=row['phone'],
                    company=row['company'],
                    created_at=row['created_at'],
                    status="active" if row['is_active'] else "inactive",
                    tier=row['tier']
                ))
                
            return customers
            
    except Exception as e:
        logger.error(f"Error getting customers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get customers: {str(e)}")

@app.post("/api/v1/customers", response_model=Customer)
async def create_customer(customer_data: CustomerCreate):
    """Create a new customer"""
    try:
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not available")
            
        customer_id = f"CUST_{uuid.uuid4().hex[:8].upper()}"
        
        # Split name into first and last name
        name_parts = customer_data.name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO customers 
                (customer_id, first_name, last_name, email, phone, company, 
                 created_at, updated_at, is_active, tier)
                VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW(), true, 'standard')
                RETURNING customer_id, first_name, last_name, email, phone, 
                         company, created_at, is_active, tier
            """, customer_id, first_name, last_name, customer_data.email, 
                customer_data.phone, customer_data.company)
            
            return Customer(
                customer_id=row['customer_id'],
                name=f"{row['first_name']} {row['last_name']}",
                email=row['email'],
                phone=row['phone'],
                company=row['company'],
                created_at=row['created_at'],
                status="active" if row['is_active'] else "inactive",
                tier=row['tier']
            )
            
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create customer: {str(e)}")

@app.get("/api/v1/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    """Get a specific customer"""
    try:
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not available")
            
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT customer_id, first_name, last_name, email, phone, 
                       company, created_at, is_active, tier
                FROM customers 
                WHERE customer_id = $1
            """, customer_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Customer not found")
                
            return Customer(
                customer_id=row['customer_id'],
                name=f"{row['first_name']} {row['last_name']}",
                email=row['email'],
                phone=row['phone'],
                company=row['company'],
                created_at=row['created_at'],
                status="active" if row['is_active'] else "inactive",
                tier=row['tier']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting customer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get customer: {str(e)}")

@app.get("/api/v1/tickets", response_model=List[Ticket])
async def get_tickets(limit: int = 50, status: Optional[str] = None):
    """Get list of tickets"""
    try:
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not available")
            
        async with db_pool.acquire() as conn:
            if status:
                rows = await conn.fetch("""
                    SELECT ticket_id, customer_id, subject, description, 
                           status, priority, created_at
                    FROM support_tickets 
                    WHERE status = $1
                    ORDER BY created_at DESC 
                    LIMIT $2
                """, status, limit)
            else:
                rows = await conn.fetch("""
                    SELECT ticket_id, customer_id, subject, description, 
                           status, priority, created_at
                    FROM support_tickets 
                    ORDER BY created_at DESC 
                    LIMIT $1
                """, limit)
            
            tickets = []
            for row in rows:
                tickets.append(Ticket(
                    ticket_id=row['ticket_id'],
                    customer_id=row['customer_id'],
                    subject=row['subject'],
                    description=row['description'],
                    status=row['status'],
                    priority=row['priority'],
                    created_at=row['created_at']
                ))
                
            return tickets
            
    except Exception as e:
        logger.error(f"Error getting tickets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tickets: {str(e)}")

@app.post("/api/v1/tickets", response_model=Ticket)
async def create_ticket(ticket_data: TicketCreate):
    """Create a new ticket"""
    try:
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not available")
            
        ticket_id = f"TKT_{uuid.uuid4().hex[:8].upper()}"
        
        async with db_pool.acquire() as conn:
            # Verify customer exists
            customer = await conn.fetchval(
                "SELECT customer_id FROM customers WHERE customer_id = $1",
                ticket_data.customer_id
            )
            if not customer:
                raise HTTPException(status_code=400, detail="Customer not found")
            
            row = await conn.fetchrow("""
                INSERT INTO support_tickets 
                (ticket_id, customer_id, subject, description, status, priority, created_at)
                VALUES ($1, $2, $3, $4, 'open', $5, NOW())
                RETURNING ticket_id, customer_id, subject, description, 
                         status, priority, created_at
            """, ticket_id, ticket_data.customer_id, ticket_data.title, 
                ticket_data.description, ticket_data.priority)
            
            return Ticket(
                ticket_id=row['ticket_id'],
                customer_id=row['customer_id'],
                subject=row['subject'],
                description=row['description'],
                status=row['status'],
                priority=row['priority'],
                created_at=row['created_at']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {str(e)}")

@app.get("/api/v1/analytics")
async def get_analytics():
    """Get system analytics"""
    try:
        if not db_pool:
            raise HTTPException(status_code=503, detail="Database not available")
            
        async with db_pool.acquire() as conn:
            # Get basic counts
            total_customers = await conn.fetchval("SELECT COUNT(*) FROM customers")
            total_tickets = await conn.fetchval("SELECT COUNT(*) FROM support_tickets")
            open_tickets = await conn.fetchval(
                "SELECT COUNT(*) FROM support_tickets WHERE status = 'open'"
            )
            resolved_tickets = await conn.fetchval(
                "SELECT COUNT(*) FROM support_tickets WHERE status = 'resolved'"
            )
            
            return {
                "total_customers": total_customers,
                "total_tickets": total_tickets,
                "open_tickets": open_tickets,
                "resolved_tickets": resolved_tickets,
                "resolution_rate": round(resolved_tickets / max(total_tickets, 1) * 100, 2)
            }
            
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
