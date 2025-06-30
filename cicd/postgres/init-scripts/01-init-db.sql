-- Initialize Agentic AI Customer Support Database
-- This script sets up the basic schema for the customer support system

-- Create schemas
CREATE SCHEMA IF NOT EXISTS customer_support;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Create users table
CREATE TABLE IF NOT EXISTS customer_support.customers (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create tickets table
CREATE TABLE IF NOT EXISTS customer_support.tickets (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(255) UNIQUE NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'open',
    priority VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customer_support.customers(customer_id)
);

-- Create queries table
CREATE TABLE IF NOT EXISTS customer_support.queries (
    id SERIAL PRIMARY KEY,
    query_id VARCHAR(255) UNIQUE NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    ticket_id VARCHAR(255),
    query_text TEXT NOT NULL,
    response_text TEXT,
    agent_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customer_support.customers(customer_id),
    FOREIGN KEY (ticket_id) REFERENCES customer_support.tickets(ticket_id)
);

-- Create feedback table
CREATE TABLE IF NOT EXISTS customer_support.feedback (
    id SERIAL PRIMARY KEY,
    query_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    satisfaction_score INTEGER CHECK (satisfaction_score >= 1 AND satisfaction_score <= 5),
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (query_id) REFERENCES customer_support.queries(query_id),
    FOREIGN KEY (customer_id) REFERENCES customer_support.customers(customer_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_customers_customer_id ON customer_support.customers(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_customer_id ON customer_support.tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON customer_support.tickets(status);
CREATE INDEX IF NOT EXISTS idx_queries_customer_id ON customer_support.queries(customer_id);
CREATE INDEX IF NOT EXISTS idx_queries_ticket_id ON customer_support.queries(ticket_id);
CREATE INDEX IF NOT EXISTS idx_queries_created_at ON customer_support.queries(created_at);

-- Insert sample data for testing
INSERT INTO customer_support.customers (customer_id, email, name) VALUES
    ('cust_001', 'john.doe@example.com', 'John Doe'),
    ('cust_002', 'jane.smith@example.com', 'Jane Smith'),
    ('cust_003', 'bob.wilson@example.com', 'Bob Wilson')
ON CONFLICT (customer_id) DO NOTHING;

INSERT INTO customer_support.tickets (ticket_id, customer_id, subject, description, status, priority) VALUES
    ('ticket_001', 'cust_001', 'Login Issues', 'Cannot access my account', 'open', 'high'),
    ('ticket_002', 'cust_002', 'Billing Question', 'Question about my last invoice', 'open', 'medium'),
    ('ticket_003', 'cust_003', 'Feature Request', 'Would like to see new features', 'closed', 'low')
ON CONFLICT (ticket_id) DO NOTHING;
