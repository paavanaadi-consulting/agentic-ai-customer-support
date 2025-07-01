"""
Customer service for handling customer-related business logic.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..api.schemas import CustomerRequest, CustomerResponse
from ..mcp.optimized_postgres_mcp_client import OptimizedPostgreSQLMCPClient, MCPClientError


class CustomerService:
    """Service class for handling customer-related business logic."""
    
    def __init__(self, 
                 mcp_client: Optional[OptimizedPostgreSQLMCPClient] = None):
        self.mcp_client = mcp_client
        # In-memory storage for demo purposes (fallback when no client provided)
        self.customers_db = {}
    
    async def create_customer(self, request: CustomerRequest) -> CustomerResponse:
        """
        Create a new customer profile.
        
        Args:
            request: CustomerRequest containing customer details
            
        Returns:
            CustomerResponse with created customer information
        """
        customer_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Validate customer data
        self._validate_customer_data(request)
        
        # Parse name into first and last name
        name_parts = request.name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        customer_data = {
            "customer_id": customer_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": request.email,
            "phone": request.phone,
            "company": request.company,
            "created_at": now,
            "tier": self._determine_customer_tier(request),
            "status": "active"
        }
        
        # Store customer using available client
        if self.mcp_client:
            try:
                created_customer = await self.mcp_client.create_customer(customer_data)
                if created_customer:
                    # Trigger welcome sequence
                    await self._trigger_welcome_sequence(customer_id)
                    
                    # Convert to response format
                    response_data = {
                        "customer_id": created_customer["customer_id"],
                        "name": f"{created_customer['first_name']} {created_customer['last_name']}".strip(),
                        "email": created_customer["email"],
                        "phone": created_customer.get("phone"),
                        "company": created_customer.get("company"),
                        "created_at": created_customer["created_at"],
                        "metadata": request.metadata,
                        "ticket_count": 0,
                        "last_interaction": None,
                        "status": created_customer["status"],
                        "tier": created_customer["tier"]
                    }
                    return CustomerResponse(**response_data)
                else:
                    raise Exception("Failed to create customer in database")
            except MCPClientError as e:
                raise Exception(f"Database error: {e}")
        
        # Fallback to in-memory storage
        customer_data_memory = {
            **customer_data,
            "name": request.name,
            "metadata": request.metadata,
            "ticket_count": 0,
            "last_interaction": None
        }
        self.customers_db[customer_id] = customer_data_memory
        
        # Trigger welcome sequence
        await self._trigger_welcome_sequence(customer_id)
        
        return CustomerResponse(**customer_data_memory)
    
    async def get_customer_by_id(self, customer_id: str) -> Optional[CustomerResponse]:
        """
        Retrieve a customer by their ID.
        
        Args:
            customer_id: The unique customer identifier
            
        Returns:
            CustomerResponse if found, None otherwise
        """
        # Try MCP client first
        if self.mcp_client:
            try:
                customer = await self.mcp_client.get_customer_by_id(customer_id)
                if customer:
                    response_data = {
                        "customer_id": customer["customer_id"],
                        "name": f"{customer['first_name']} {customer['last_name']}".strip(),
                        "email": customer["email"],
                        "phone": customer.get("phone"),
                        "company": customer.get("company"),
                        "created_at": customer["created_at"],
                        "metadata": {},  # Not stored in database schema
                        "ticket_count": 0,  # TODO: Calculate from tickets
                        "last_interaction": customer.get("last_interaction"),
                        "status": customer["status"],
                        "tier": customer["tier"]
                    }
                    return CustomerResponse(**response_data)
            except MCPClientError as e:
                # Log error but continue to fallback
                print(f"MCP client error: {e}")
        
        # Fallback to in-memory storage
        if customer_id not in self.customers_db:
            return None
        
        customer = self.customers_db[customer_id]
        return CustomerResponse(**customer)
    
    async def get_customer_by_email(self, email: str) -> Optional[CustomerResponse]:
        """
        Retrieve a customer by their email address.
        
        Args:
            email: The customer's email address
            
        Returns:
            CustomerResponse if found, None otherwise
        """
        for customer in self.customers_db.values():
            if customer["email"].lower() == email.lower():
                return CustomerResponse(**customer)
        return None
    
    async def update_customer(
        self, 
        customer_id: str, 
        updates: Dict[str, Any]
    ) -> Optional[CustomerResponse]:
        """
        Update customer information.
        
        Args:
            customer_id: The unique customer identifier
            updates: Dictionary of fields to update
            
        Returns:
            Updated CustomerResponse if found, None otherwise
        """
        if customer_id not in self.customers_db:
            return None
        
        # Validate updates
        allowed_fields = {
            "name", "email", "phone", "company", "metadata"
        }
        
        for field in updates:
            if field not in allowed_fields:
                raise ValueError(f"Field '{field}' cannot be updated")
        
        # Apply updates
        customer = self.customers_db[customer_id]
        for field, value in updates.items():
            customer[field] = value
        
        customer["updated_at"] = datetime.utcnow()
        
        return CustomerResponse(**customer)
    
    async def list_customers(self, limit: int = 100) -> List[CustomerResponse]:
        """
        List customers.
        
        Args:
            limit: Maximum number of customers to return
            
        Returns:
            List of CustomerResponse objects
        """
        customers = []
        
        # Try MCP client first
        if self.mcp_client:
            try:
                customer_data = await self.mcp_client.get_customers(limit=limit)
                for customer in customer_data:
                    response_data = {
                        "customer_id": customer["customer_id"],
                        "name": f"{customer['first_name']} {customer['last_name']}".strip(),
                        "email": customer["email"],
                        "phone": customer.get("phone"),
                        "company": customer.get("company"),
                        "created_at": customer["created_at"],
                        "metadata": {},  # Not stored in database schema
                        "ticket_count": 0,  # TODO: Calculate from tickets
                        "last_interaction": customer.get("last_interaction"),
                        "status": customer["status"],
                        "tier": customer["tier"]
                    }
                    customers.append(CustomerResponse(**response_data))
                return customers
            except MCPClientError as e:
                # Log error but continue to fallback
                print(f"MCP client error: {e}")
        
        # Fallback to in-memory storage
        for customer_data in list(self.customers_db.values())[:limit]:
            customers.append(CustomerResponse(**customer_data))
        
        return customers
    
    async def update_last_interaction(self, customer_id: str) -> None:
        """
        Update the last interaction timestamp for a customer.
        
        Args:
            customer_id: The unique customer identifier
        """
        # Use MCP client if available
        if self.mcp_client:
            try:
                await self.mcp_client.update_customer(customer_id, {
                    "last_interaction": datetime.utcnow()
                })
                return
            except MCPClientError as e:
                # Log error and fall back to in-memory
                print(f"MCP error in update_last_interaction: {e}")
                pass
        
        # Fallback to in-memory storage
        if customer_id in self.customers_db:
            self.customers_db[customer_id]["last_interaction"] = datetime.utcnow()
    
    async def increment_ticket_count(self, customer_id: str) -> None:
        """
        Increment the ticket count for a customer.
        
        Args:
            customer_id: The unique customer identifier
        """
        # Use MCP client if available
        if self.mcp_client:
            try:
                # Get current customer data
                customer = await self.mcp_client.get_customer_by_id(customer_id)
                if customer:
                    current_count = customer.get("total_tickets", 0)
                    await self.mcp_client.update_customer(customer_id, {
                        "total_tickets": current_count + 1
                    })
                    await self._check_tier_upgrade(customer_id)
                return
            except MCPClientError as e:
                # Log error and fall back to in-memory
                print(f"MCP error in increment_ticket_count: {e}")
                pass
        
        # Fallback to in-memory storage
        if customer_id in self.customers_db:
            self.customers_db[customer_id]["ticket_count"] += 1
            await self._check_tier_upgrade(customer_id)
    
    async def get_customer_summary(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a comprehensive summary of customer activity.
        
        Args:
            customer_id: The unique customer identifier
            
        Returns:
            Dictionary with customer summary or None if not found
        """
        if customer_id not in self.customers_db:
            return None
        
        customer = self.customers_db[customer_id]
        
        # Calculate additional metrics
        days_since_creation = (
            datetime.utcnow() - customer["created_at"]
        ).days
        
        last_interaction_days = None
        if customer.get("last_interaction"):
            last_interaction_days = (
                datetime.utcnow() - customer["last_interaction"]
            ).days
        
        return {
            "customer_id": customer_id,
            "basic_info": {
                "name": customer["name"],
                "email": customer["email"],
                "company": customer.get("company"),
                "tier": customer.get("tier", "standard")
            },
            "activity_metrics": {
                "ticket_count": customer["ticket_count"],
                "days_since_creation": days_since_creation,
                "last_interaction_days": last_interaction_days,
                "status": customer.get("status", "active")
            },
            "engagement_score": self._calculate_engagement_score(customer)
        }
    
    def _validate_customer_data(self, request: CustomerRequest) -> None:
        """
        Validate customer data before creation.
        
        Args:
            request: CustomerRequest to validate
            
        Raises:
            ValueError: If validation fails
        """
        # Check for duplicate email
        for customer in self.customers_db.values():
            if customer["email"].lower() == request.email.lower():
                raise ValueError(f"Customer with email {request.email} already exists")
        
        # Validate email format (basic check)
        if "@" not in request.email or "." not in request.email:
            raise ValueError("Invalid email format")
        
        # Validate name
        if len(request.name.strip()) < 2:
            raise ValueError("Customer name must be at least 2 characters")
    
    def _determine_customer_tier(self, request: CustomerRequest) -> str:
        """
        Determine customer tier based on initial information.
        
        Args:
            request: CustomerRequest
            
        Returns:
            Customer tier string
        """
        # Simple tier determination logic
        if request.company:
            return "business"
        else:
            return "standard"
    
    async def _trigger_welcome_sequence(self, customer_id: str) -> None:
        """
        Trigger welcome sequence for new customers.
        
        Args:
            customer_id: The unique customer identifier
        """
        # In a real implementation, this would:
        # - Send welcome email
        # - Create onboarding tasks
        # - Set up initial preferences
        pass
    
    async def _check_tier_upgrade(self, customer_id: str) -> None:
        """
        Check if customer qualifies for tier upgrade.
        
        Args:
            customer_id: The unique customer identifier
        """
        customer = self.customers_db[customer_id]
        current_tier = customer.get("tier", "standard")
        
        # Upgrade logic based on ticket count and other factors
        if (current_tier == "standard" and 
            customer["ticket_count"] >= 10):
            customer["tier"] = "premium"
        elif (current_tier == "premium" and 
              customer["ticket_count"] >= 50):
            customer["tier"] = "enterprise"
    
    def _calculate_engagement_score(self, customer: Dict[str, Any]) -> float:
        """
        Calculate customer engagement score.
        
        Args:
            customer: Customer data dictionary
            
        Returns:
            Engagement score between 0.0 and 1.0
        """
        score = 0.0
        
        # Base score for being active
        if customer.get("status") == "active":
            score += 0.3
        
        # Score based on ticket activity
        ticket_count = customer.get("ticket_count", 0)
        if ticket_count > 0:
            score += min(0.3, ticket_count * 0.05)
        
        # Score based on recency of interaction
        if customer.get("last_interaction"):
            days_since = (
                datetime.utcnow() - customer["last_interaction"]
            ).days
            if days_since <= 7:
                score += 0.4
            elif days_since <= 30:
                score += 0.2
            elif days_since <= 90:
                score += 0.1
        
        return min(1.0, score)
    
    def get_customer_count(self) -> int:
        """Get total number of customers."""
        return len(self.customers_db)
    
    def get_customers_by_tier(self) -> Dict[str, int]:
        """Get customer count by tier."""
        customers_by_tier = {}
        for customer in self.customers_db.values():
            tier = customer.get("tier", "standard")
            customers_by_tier[tier] = customers_by_tier.get(tier, 0) + 1
        return customers_by_tier
