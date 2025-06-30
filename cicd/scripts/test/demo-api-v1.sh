#!/bin/bash
# Demo script for API V1 endpoints

set -e

API_BASE="http://localhost:8080/api/v1"

echo "🚀 Agentic AI Customer Support API V1 Demo"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${BLUE}📊 API Status:${NC}"
curl -s $API_BASE/status | python3 -m json.tool
echo ""

echo -e "${BLUE}🔍 Processing a customer query:${NC}"
QUERY_RESPONSE=$(curl -s -X POST $API_BASE/queries \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I cannot access my account. What should I do?",
    "customer_id": "demo-customer-001",
    "query_type": "account",
    "priority": "high"
  }')

echo "$QUERY_RESPONSE" | python3 -m json.tool
QUERY_ID=$(echo "$QUERY_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['query_id'])")
echo ""

echo -e "${BLUE}🎫 Creating a support ticket:${NC}"
TICKET_RESPONSE=$(curl -s -X POST $API_BASE/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Account access issues",
    "description": "Customer reports difficulty accessing account after password reset attempt",
    "customer_id": "demo-customer-001",
    "category": "account",
    "priority": "high",
    "tags": ["account", "login", "password"]
  }')

echo "$TICKET_RESPONSE" | python3 -m json.tool
TICKET_ID=$(echo "$TICKET_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['ticket_id'])")
echo ""

echo -e "${BLUE}👤 Creating a customer profile:${NC}"
CUSTOMER_RESPONSE=$(curl -s -X POST $API_BASE/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-0123",
    "company": "Demo Corp",
    "metadata": {"segment": "enterprise", "region": "us-west"}
  }')

echo "$CUSTOMER_RESPONSE" | python3 -m json.tool
CUSTOMER_ID=$(echo "$CUSTOMER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['customer_id'])")
echo ""

echo -e "${BLUE}⭐ Submitting customer feedback:${NC}"
curl -s -X POST $API_BASE/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "'$CUSTOMER_ID'",
    "rating": 4,
    "comment": "Great support! The agent was very helpful.",
    "query_id": "'$QUERY_ID'",
    "ticket_id": "'$TICKET_ID'"
  }' | python3 -m json.tool
echo ""

echo -e "${BLUE}📈 System analytics:${NC}"
curl -s $API_BASE/analytics | python3 -m json.tool
echo ""

echo -e "${BLUE}📋 Listing recent queries:${NC}"
curl -s "$API_BASE/queries?limit=5" | python3 -m json.tool
echo ""

echo -e "${BLUE}🎫 Listing tickets:${NC}"
curl -s "$API_BASE/tickets?limit=5" | python3 -m json.tool
echo ""

echo -e "${GREEN}✅ Demo completed!${NC}"
echo ""
echo -e "${YELLOW}📖 Available endpoints:${NC}"
echo "  • POST /api/v1/queries - Process customer queries"
echo "  • GET  /api/v1/queries - List queries"
echo "  • POST /api/v1/tickets - Create support tickets"
echo "  • GET  /api/v1/tickets - List tickets"
echo "  • POST /api/v1/customers - Create customers"
echo "  • GET  /api/v1/customers - List customers"
echo "  • POST /api/v1/feedback - Submit feedback"
echo "  • GET  /api/v1/analytics - Get system metrics"
echo "  • GET  /api/v1/status - API status"
echo ""
echo -e "${YELLOW}📚 Full documentation: http://localhost:8080/docs${NC}"
