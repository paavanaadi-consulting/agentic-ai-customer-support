# API Reference

## Endpoints

### POST /query
- **Description:** Submit a customer query for processing.
- **Request Body:**
  - `query`: str
  - `customer_id`: str
  - `context`: dict (optional)
- **Response:**
  - `result`: str or dict
  - `success`: bool

## Example
```json
{
  "query": "How do I reset my password?",
  "customer_id": "cust_001",
  "context": {}
}
```
