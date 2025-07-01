"""
Customer service for handling customer-related business logic.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from ..api.schemas import CustomerRequest, CustomerResponse


class CustomerService:
    """Service class for handling customer-related business logic."""
    
    def __init__(self):
        # In-memory storage for demo purposes (replace with database in production)
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
        
        customer_data = {
            "customer_id": customer_id,
            "name": request.name,
            "email": request.email,
            "phone": request.phone,
            "company": request.company,
            "created_at": now,
            "metadata": request.metadata,
            "ticket_count": 0,
            "last_interaction": None,
            "status": "active",
            "tier": self._determine_customer_tier(request)
        }
        
        # Store customer
        self.customers_db[customer_id] = customer_data
        
        # Trigger welcome sequence
        await self._trigger_welcome_sequence(customer_id)
        
        return CustomerResponse(**customer_data)
    
    async def get_customer_by_id(self, customer_id: str) -> Optional[CustomerResponse]:
        """
        Retrieve a customer by their ID.
        
        Args:
            customer_id: The unique customer identifier
            
        Returns:
            CustomerResponse if found, None otherwise
        """
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
    
    async def list_customers(self, limit: int = 10) -> List[CustomerResponse]:
        """
        List all customers with pagination.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of CustomerResponse objects
        """
        customers = list(self.customers_db.values())
        
        # Sort by creation date (newest first)
        customers.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply limit
        customers = customers[:limit]
        
        return [CustomerResponse(**customer) for customer in customers]
    
    async def update_last_interaction(self, customer_id: str) -> None:
        """
        Update the last interaction timestamp for a customer.
        
        Args:
            customer_id: The unique customer identifier
        """
        if customer_id in self.customers_db:
            self.customers_db[customer_id]["last_interaction"] = datetime.utcnow()
    
    async def increment_ticket_count(self, customer_id: str) -> None:
        """
        Increment the ticket count for a customer.
        
        Args:
            customer_id: The unique customer identifier
        """
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
