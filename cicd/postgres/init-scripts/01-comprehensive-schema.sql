-- =====================================================
-- Customer Support Database Schema
-- PostgreSQL Data Model for Genetic AI Support System
-- Combined comprehensive schema and initialization script
-- =====================================================

-- Drop existing tables if they exist (for clean setup)
DROP TABLE IF EXISTS agent_performance CASCADE;
DROP TABLE IF EXISTS query_interactions CASCADE;
DROP TABLE IF EXISTS ticket_responses CASCADE;
DROP TABLE IF EXISTS ticket_attachments CASCADE;
DROP TABLE IF EXISTS support_tickets CASCADE;
DROP TABLE IF EXISTS knowledge_article_feedback CASCADE;
DROP TABLE IF EXISTS knowledge_articles CASCADE;
DROP TABLE IF EXISTS customer_feedback CASCADE;
DROP TABLE IF EXISTS customer_sessions CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS agents CASCADE;
DROP TABLE IF EXISTS departments CASCADE;

-- Drop existing schemas from old init script
DROP SCHEMA IF EXISTS customer_support CASCADE;
DROP SCHEMA IF EXISTS analytics CASCADE;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- CORE TABLES
-- =====================================================

-- Departments table
CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories for support tickets and knowledge articles
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    parent_category_id INTEGER REFERENCES categories(id),
    color_code VARCHAR(7) DEFAULT '#007bff',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Human agents/staff members
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    department_id INTEGER REFERENCES departments(id),
    role VARCHAR(50) DEFAULT 'agent', -- agent, supervisor, admin
    is_active BOOLEAN DEFAULT TRUE,
    skills TEXT[], -- Array of skills/specializations
    max_concurrent_tickets INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    phone VARCHAR(50),
    company VARCHAR(255),
    tier VARCHAR(50) DEFAULT 'standard', -- free, standard, premium, enterprise
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT TRUE,
    total_tickets INTEGER DEFAULT 0,
    satisfaction_avg DECIMAL(3,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer sessions for tracking interactions
CREATE TABLE customer_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    customer_id VARCHAR(255) REFERENCES customers(customer_id),
    ip_address INET,
    user_agent TEXT,
    referrer TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    page_views INTEGER DEFAULT 0,
    duration_seconds INTEGER DEFAULT 0
);

-- =====================================================
-- SUPPORT TICKETS
-- =====================================================

-- Main support tickets table
CREATE TABLE support_tickets (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(255) NOT NULL UNIQUE,
    customer_id VARCHAR(255) REFERENCES customers(customer_id),
    assigned_agent_id INTEGER REFERENCES agents(id),
    category_id INTEGER REFERENCES categories(id),
    subject VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'open', -- open, in_progress, waiting_customer, resolved, closed
    priority VARCHAR(50) DEFAULT 'medium', -- low, medium, high, urgent, critical
    source VARCHAR(50) DEFAULT 'web', -- web, email, chat, phone, api
    tags TEXT[], -- Array of tags for categorization
    estimated_resolution_time INTERVAL,
    actual_resolution_time INTERVAL,
    first_response_at TIMESTAMP,
    resolved_at TIMESTAMP,
    closed_at TIMESTAMP,
    satisfaction_score INTEGER CHECK (satisfaction_score >= 1 AND satisfaction_score <= 5),
    satisfaction_comment TEXT,
    internal_notes TEXT,
    escalation_level INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ticket responses/messages
CREATE TABLE ticket_responses (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(255) REFERENCES support_tickets(ticket_id),
    responder_type VARCHAR(20) NOT NULL, -- customer, agent, ai_agent, system
    responder_id VARCHAR(255), -- Could be agent_id, customer_id, or ai_agent_id
    responder_name VARCHAR(255),
    message TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'reply', -- reply, note, status_change, escalation
    is_internal BOOLEAN DEFAULT FALSE,
    is_auto_generated BOOLEAN DEFAULT FALSE,
    processing_time_ms INTEGER,
    ai_confidence_score DECIMAL(4,3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ticket attachments
CREATE TABLE ticket_attachments (
    id SERIAL PRIMARY KEY,
    ticket_id VARCHAR(255) REFERENCES support_tickets(ticket_id),
    response_id INTEGER REFERENCES ticket_responses(id),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100),
    file_path TEXT NOT NULL,
    uploaded_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- KNOWLEDGE BASE
-- =====================================================

-- Knowledge base articles
CREATE TABLE knowledge_articles (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR(255) NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    category_id INTEGER REFERENCES categories(id),
    author_id INTEGER REFERENCES agents(id),
    status VARCHAR(50) DEFAULT 'draft', -- draft, published, archived
    tags TEXT[],
    keywords TEXT[],
    language VARCHAR(10) DEFAULT 'en',
    version INTEGER DEFAULT 1,
    views_count INTEGER DEFAULT 0,
    helpful_votes INTEGER DEFAULT 0,
    unhelpful_votes INTEGER DEFAULT 0,
    search_vector tsvector, -- For full-text search
    last_reviewed_at TIMESTAMP,
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Knowledge article feedback
CREATE TABLE knowledge_article_feedback (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR(255) REFERENCES knowledge_articles(article_id),
    customer_id VARCHAR(255) REFERENCES customers(customer_id),
    feedback_type VARCHAR(20) NOT NULL, -- helpful, unhelpful, suggestion
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- AI SYSTEM TABLES
-- =====================================================

-- Query interactions for AI learning
CREATE TABLE query_interactions (
    id SERIAL PRIMARY KEY,
    query_id VARCHAR(255) NOT NULL UNIQUE,
    session_id VARCHAR(255) REFERENCES customer_sessions(session_id),
    customer_id VARCHAR(255) REFERENCES customers(customer_id),
    ticket_id VARCHAR(255) REFERENCES support_tickets(ticket_id),
    query_text TEXT NOT NULL,
    query_type VARCHAR(50), -- question, complaint, request, compliment
    detected_language VARCHAR(10) DEFAULT 'en',
    detected_intent VARCHAR(100),
    detected_entities JSONB,
    sentiment VARCHAR(20), -- positive, negative, neutral
    sentiment_score DECIMAL(4,3),
    urgency_level VARCHAR(20), -- low, medium, high, critical
    urgency_score DECIMAL(4,3),
    category_prediction VARCHAR(100),
    category_confidence DECIMAL(4,3),
    response_text TEXT,
    response_type VARCHAR(50), -- direct_answer, escalation, knowledge_base
    response_sources JSONB, -- Sources used for generating response
    processing_time_ms INTEGER,
    total_processing_time_ms INTEGER,
    agents_used TEXT[], -- Array of AI agents that processed this query
    success_metrics JSONB,
    customer_satisfaction INTEGER CHECK (customer_satisfaction >= 1 AND customer_satisfaction <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Agent performance tracking
CREATE TABLE agent_performance (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50) NOT NULL, -- query, knowledge, response
    generation INTEGER DEFAULT 0,
    chromosome_id UUID DEFAULT uuid_generate_v4(),
    fitness_score DECIMAL(6,4),
    genes JSONB NOT NULL,
    performance_metrics JSONB,
    test_results JSONB,
    training_data_size INTEGER,
    validation_accuracy DECIMAL(6,4),
    avg_response_time_ms DECIMAL(10,2),
    success_rate DECIMAL(6,4),
    customer_satisfaction_avg DECIMAL(4,3),
    queries_processed INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer feedback for continuous improvement
CREATE TABLE customer_feedback (
    id SERIAL PRIMARY KEY,
    feedback_id VARCHAR(255) NOT NULL UNIQUE,
    customer_id VARCHAR(255) REFERENCES customers(customer_id),
    ticket_id VARCHAR(255) REFERENCES support_tickets(ticket_id),
    query_id VARCHAR(255) REFERENCES query_interactions(query_id),
    feedback_type VARCHAR(50), -- satisfaction, suggestion, complaint, compliment
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    tags TEXT[],
    is_processed BOOLEAN DEFAULT FALSE,
    action_taken TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Customer indexes
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_tier ON customers(tier);
CREATE INDEX idx_customers_created_at ON customers(created_at);

-- Ticket indexes
CREATE INDEX idx_support_tickets_customer_id ON support_tickets(customer_id);
CREATE INDEX idx_support_tickets_status ON support_tickets(status);
CREATE INDEX idx_support_tickets_priority ON support_tickets(priority);
CREATE INDEX idx_support_tickets_category_id ON support_tickets(category_id);
CREATE INDEX idx_support_tickets_assigned_agent_id ON support_tickets(assigned_agent_id);
CREATE INDEX idx_support_tickets_created_at ON support_tickets(created_at);
CREATE INDEX idx_support_tickets_resolved_at ON support_tickets(resolved_at);

-- Response indexes
CREATE INDEX idx_ticket_responses_ticket_id ON ticket_responses(ticket_id);
CREATE INDEX idx_ticket_responses_created_at ON ticket_responses(created_at);
CREATE INDEX idx_ticket_responses_responder_type ON ticket_responses(responder_type);

-- Knowledge base indexes
CREATE INDEX idx_knowledge_articles_category_id ON knowledge_articles(category_id);
CREATE INDEX idx_knowledge_articles_status ON knowledge_articles(status);
CREATE INDEX idx_knowledge_articles_published_at ON knowledge_articles(published_at);
CREATE INDEX idx_knowledge_articles_search_vector ON knowledge_articles USING gin(search_vector);

-- AI system indexes
CREATE INDEX idx_query_interactions_customer_id ON query_interactions(customer_id);
CREATE INDEX idx_query_interactions_created_at ON query_interactions(created_at);
CREATE INDEX idx_query_interactions_category_prediction ON query_interactions(category_prediction);
CREATE INDEX idx_query_interactions_sentiment ON query_interactions(sentiment);

CREATE INDEX idx_agent_performance_agent_id ON agent_performance(agent_id);
CREATE INDEX idx_agent_performance_generation ON agent_performance(generation);
CREATE INDEX idx_agent_performance_fitness_score ON agent_performance(fitness_score);
CREATE INDEX idx_agent_performance_created_at ON agent_performance(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_tickets_status_priority ON support_tickets(status, priority);
CREATE INDEX idx_tickets_customer_status ON support_tickets(customer_id, status);
CREATE INDEX idx_interactions_customer_date ON query_interactions(customer_id, created_at);

-- =====================================================
-- FULL-TEXT SEARCH SETUP
-- =====================================================

-- Create full-text search index for knowledge articles
CREATE OR REPLACE FUNCTION update_knowledge_article_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.content, '') || ' ' || COALESCE(array_to_string(NEW.keywords, ' '), ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_knowledge_article_search_vector_trigger
    BEFORE INSERT OR UPDATE ON knowledge_articles
    FOR EACH ROW EXECUTE FUNCTION update_knowledge_article_search_vector();

-- =====================================================
-- FUNCTIONS AND TRIGGERS
-- =====================================================

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updating timestamps
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_support_tickets_updated_at BEFORE UPDATE ON support_tickets 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_articles_updated_at BEFORE UPDATE ON knowledge_articles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update customer statistics
CREATE OR REPLACE FUNCTION update_customer_stats() RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE customers 
        SET total_tickets = total_tickets + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE customer_id = NEW.customer_id;
    ELSIF TG_OP = 'UPDATE' AND OLD.satisfaction_score IS NULL AND NEW.satisfaction_score IS NOT NULL THEN
        UPDATE customers 
        SET satisfaction_avg = (
            SELECT AVG(satisfaction_score)::DECIMAL(3,2) 
            FROM support_tickets 
            WHERE customer_id = NEW.customer_id AND satisfaction_score IS NOT NULL
        ),
        updated_at = CURRENT_TIMESTAMP
        WHERE customer_id = NEW.customer_id;
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_customer_stats_trigger
    AFTER INSERT OR UPDATE ON support_tickets
    FOR EACH ROW EXECUTE FUNCTION update_customer_stats();

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Customer summary view
CREATE VIEW customer_summary AS
SELECT 
    c.customer_id,
    c.email,
    c.first_name,
    c.last_name,
    c.tier,
    c.total_tickets,
    c.satisfaction_avg,
    COUNT(st.id) FILTER (WHERE st.status = 'open') as open_tickets,
    COUNT(st.id) FILTER (WHERE st.status = 'resolved') as resolved_tickets,
    AVG(EXTRACT(epoch FROM (st.resolved_at - st.created_at))/3600) FILTER (WHERE st.resolved_at IS NOT NULL) as avg_resolution_hours,
    c.created_at as customer_since,
    c.last_seen_at
FROM customers c
LEFT JOIN support_tickets st ON c.customer_id = st.customer_id
GROUP BY c.customer_id, c.email, c.first_name, c.last_name, c.tier, c.total_tickets, c.satisfaction_avg, c.created_at, c.last_seen_at;

-- Agent performance view
CREATE VIEW agent_performance_summary AS
SELECT 
    a.agent_id,
    a.name,
    a.email,
    d.name as department,
    COUNT(st.id) as total_tickets,
    COUNT(st.id) FILTER (WHERE st.status = 'resolved') as resolved_tickets,
    AVG(st.satisfaction_score) as avg_satisfaction,
    AVG(EXTRACT(epoch FROM (st.first_response_at - st.created_at))/60) as avg_first_response_minutes,
    AVG(EXTRACT(epoch FROM (st.resolved_at - st.created_at))/3600) FILTER (WHERE st.resolved_at IS NOT NULL) as avg_resolution_hours
FROM agents a
LEFT JOIN departments d ON a.department_id = d.id
LEFT JOIN support_tickets st ON a.id = st.assigned_agent_id
GROUP BY a.agent_id, a.name, a.email, d.name;

-- Ticket analytics view
CREATE VIEW ticket_analytics AS
SELECT 
    DATE_TRUNC('day', created_at) as date,
    COUNT(*) as total_tickets,
    COUNT(*) FILTER (WHERE priority = 'urgent') as urgent_tickets,
    COUNT(*) FILTER (WHERE priority = 'high') as high_priority_tickets,
    COUNT(*) FILTER (WHERE status = 'resolved') as resolved_tickets,
    AVG(satisfaction_score) as avg_satisfaction,
    AVG(EXTRACT(epoch FROM (resolved_at - created_at))/3600) FILTER (WHERE resolved_at IS NOT NULL) as avg_resolution_hours
FROM support_tickets
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;

-- AI performance view
CREATE VIEW ai_agent_performance AS
SELECT 
    agent_id,
    agent_type,
    generation,
    fitness_score,
    performance_metrics->>'success_rate' as success_rate,
    performance_metrics->>'avg_response_time' as avg_response_time,
    performance_metrics->>'customer_satisfaction' as customer_satisfaction,
    queries_processed,
    created_at
FROM agent_performance
WHERE is_active = TRUE
ORDER BY agent_id, generation DESC;

-- =====================================================
-- SAMPLE DATA GENERATION
-- =====================================================

-- Insert departments
INSERT INTO departments (name, description, email) VALUES
('Technical Support', 'Handles technical issues and troubleshooting', 'tech-support@company.com'),
('Billing Support', 'Manages billing inquiries and payment issues', 'billing@company.com'),
('Customer Success', 'Focuses on customer onboarding and success', 'success@company.com'),
('Product Support', 'Assists with product features and usage', 'product@company.com');

-- Insert categories
INSERT INTO categories (name, description, color_code) VALUES
('Technical Issues', 'Software bugs, system errors, performance problems', '#dc3545'),
('Billing & Payments', 'Payment processing, invoicing, subscription management', '#28a745'),
('Account Management', 'Login issues, password resets, account settings', '#007bff'),
('Product Features', 'Feature requests, how-to questions, tutorials', '#17a2b8'),
('General Inquiry', 'General questions and information requests', '#6c757d'),
('Bug Reports', 'Software defects and error reports', '#fd7e14'),
('Feature Requests', 'New feature suggestions and enhancements', '#6f42c1'),
('Integration Support', 'API and third-party integration assistance', '#20c997');

-- Insert subcategories
INSERT INTO categories (name, description, parent_category_id, color_code) VALUES
('Login Problems', 'Cannot access account, authentication issues', 3, '#0056b3'),
('API Issues', 'REST API problems and documentation', 8, '#17a085'),
('Payment Failures', 'Credit card declined, payment processing errors', 2, '#1e7e34'),
('Performance Issues', 'Slow loading, timeouts, system lag', 1, '#bd2130'),
('Mobile App', 'Mobile application specific issues', 1, '#e83e8c'),
('Web Dashboard', 'Web interface problems and questions', 4, '#795548');

-- Insert agents
INSERT INTO agents (agent_id, name, email, department_id, role, skills, max_concurrent_tickets) VALUES
('AGT001', 'Sarah Johnson', 'sarah.johnson@company.com', 1, 'senior_agent', ARRAY['Python', 'JavaScript', 'Database', 'API'], 15),
('AGT002', 'Mike Chen', 'mike.chen@company.com', 1, 'agent', ARRAY['Frontend', 'React', 'CSS', 'UI/UX'], 12),
('AGT003', 'Emily Davis', 'emily.davis@company.com', 2, 'supervisor', ARRAY['Billing', 'Payments', 'Accounting', 'Leadership'], 20),
('AGT004', 'David Rodriguez', 'david.rodriguez@company.com', 2, 'agent', ARRAY['Customer Service', 'Payment Processing', 'Stripe'], 10),
('AGT005', 'Lisa Wang', 'lisa.wang@company.com', 3, 'agent', ARRAY['Onboarding', 'Training', 'Customer Success'], 8),
('AGT006', 'James Smith', 'james.smith@company.com', 4, 'senior_agent', ARRAY['Product Management', 'Feature Design', 'Analytics'], 12);

-- Insert customers with realistic data
INSERT INTO customers (customer_id, email, first_name, last_name, company, tier, language, timezone) VALUES
('CUST_001', 'john.doe@techcorp.com', 'John', 'Doe', 'TechCorp Inc.', 'enterprise', 'en', 'America/New_York'),
('CUST_002', 'jane.smith@startup.io', 'Jane', 'Smith', 'Startup.io', 'premium', 'en', 'America/Los_Angeles'),
('CUST_003', 'bob.wilson@freelance.com', 'Bob', 'Wilson', NULL, 'standard', 'en', 'America/Chicago'),
('CUST_004', 'alice.brown@company.co.uk', 'Alice', 'Brown', 'Company Ltd', 'premium', 'en', 'Europe/London'),
('CUST_005', 'carlos.martinez@empresa.es', 'Carlos', 'Martinez', 'Empresa SA', 'standard', 'es', 'Europe/Madrid'),
('CUST_006', 'yuki.tanaka@company.jp', 'Yuki', 'Tanaka', 'Company KK', 'enterprise', 'ja', 'Asia/Tokyo'),
('CUST_007', 'marie.dubois@societe.fr', 'Marie', 'Dubois', 'Société SARL', 'premium', 'fr', 'Europe/Paris'),
('CUST_008', 'peter.mueller@firma.de', 'Peter', 'Mueller', 'Firma GmbH', 'enterprise', 'de', 'Europe/Berlin'),
('CUST_009', 'anna.kowalski@firma.pl', 'Anna', 'Kowalski', 'Firma Sp. z o.o.', 'standard', 'pl', 'Europe/Warsaw'),
('CUST_010', 'raj.patel@business.in', 'Raj', 'Patel', 'Business Pvt Ltd', 'premium', 'en', 'Asia/Kolkata');

-- Insert customer sessions
INSERT INTO customer_sessions (session_id, customer_id, ip_address, user_agent, page_views, duration_seconds) VALUES
('SESS_001', 'CUST_001', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 15, 1200),
('SESS_002', 'CUST_002', '10.0.0.50', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', 8, 450),
('SESS_003', 'CUST_003', '172.16.0.25', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36', 22, 1800),
('SESS_004', 'CUST_004', '203.0.113.10', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101', 12, 900),
('SESS_005', 'CUST_005', '198.51.100.15', 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)', 5, 300);

-- Insert support tickets with comprehensive test data
INSERT INTO support_tickets (ticket_id, customer_id, assigned_agent_id, category_id, subject, description, status, priority, source, tags) VALUES
('TKT_001', 'CUST_001', 1, 1, 'API returning 500 errors intermittently', 'Our production system is experiencing intermittent 500 errors when calling the /api/v1/users endpoint. This started about 2 hours ago and is affecting approximately 15% of our requests.', 'in_progress', 'high', 'api', ARRAY['api', '500-error', 'production', 'urgent']),
('TKT_002', 'CUST_002', 4, 2, 'Payment failed but money was charged', 'I tried to upgrade my subscription yesterday but the payment failed with an error message. However, I see the charge on my credit card statement. Can you please help resolve this?', 'open', 'medium', 'web', ARRAY['payment', 'billing', 'subscription', 'upgrade']),
('TKT_003', 'CUST_003', 2, 3, 'Cannot log into my account', 'I have been trying to log into my account for the past hour but keep getting "Invalid credentials" error. I am sure I am using the correct email and password. I tried password reset but did not receive any email.', 'resolved', 'medium', 'email', ARRAY['login', 'authentication', 'password-reset']),
('TKT_004', 'CUST_004', 6, 4, 'How to integrate webhooks with Slack?', 'I want to set up webhooks to send notifications to our Slack channel when certain events occur in our application. Could you provide documentation or examples on how to configure this?', 'resolved', 'low', 'chat', ARRAY['webhooks', 'integration', 'slack', 'documentation']),
('TKT_005', 'CUST_005', 3, 2, 'Invoice not received this month', 'I have not received my invoice for this month. Could you please resend it to my email? I need the invoice for my accounting.', 'open', 'low', 'email', ARRAY['invoice', 'billing', 'accounting']);

-- Update some tickets with resolution info
UPDATE support_tickets SET 
    status = 'resolved',
    resolved_at = created_at + interval '4 hours',
    first_response_at = created_at + interval '15 minutes',
    satisfaction_score = 5,
    satisfaction_comment = 'Very helpful and quick response!'
WHERE ticket_id = 'TKT_003';

UPDATE support_tickets SET 
    status = 'resolved',
    resolved_at = created_at + interval '2 hours',
    first_response_at = created_at + interval '5 minutes',
    satisfaction_score = 4,
    satisfaction_comment = 'Good documentation provided'
WHERE ticket_id = 'TKT_004';

-- Insert sample ticket responses for demonstration
INSERT INTO ticket_responses (ticket_id, responder_type, responder_id, responder_name, message, message_type, is_internal, is_auto_generated, processing_time_ms, ai_confidence_score) VALUES
('TKT_001', 'ai_agent', 'query_agent', 'AI Query Agent', 'I understand you are experiencing intermittent 500 errors with the /api/v1/users endpoint. This appears to be a high-priority technical issue that requires immediate attention. Let me analyze this and escalate to our technical team.', 'reply', FALSE, TRUE, 250, 0.95),
('TKT_001', 'agent', 'AGT001', 'Sarah Johnson', 'Thank you for reporting this API issue. I can see the elevated error rates in our monitoring dashboard. Our backend team is investigating the root cause. I will update you within 30 minutes with our findings.', 'reply', FALSE, FALSE, NULL, NULL),
('TKT_002', 'ai_agent', 'query_agent', 'AI Query Agent', 'I understand you are experiencing a payment issue where your subscription upgrade failed but you were still charged. This is definitely frustrating and we will resolve this immediately. Let me connect you with our billing specialist.', 'reply', FALSE, TRUE, 320, 0.92),
('TKT_002', 'agent', 'AGT004', 'David Rodriguez', 'Hi Jane, I have reviewed your account and can see the charge on your card. The upgrade process was interrupted due to a payment gateway timeout. Let me process your upgrade manually right now.', 'reply', FALSE, FALSE, NULL, NULL),
('TKT_003', 'ai_agent', 'query_agent', 'AI Query Agent', 'I see you are having trouble logging into your account with "Invalid credentials" errors. This is a common authentication issue that we can resolve quickly. Let me check your account status.', 'reply', FALSE, TRUE, 280, 0.90),
('TKT_003', 'agent', 'AGT002', 'Mike Chen', 'Hi Bob, I found that your email was marked as bounced due to a server issue. I have cleared the bounce flag and reset your password. Please check your email now.', 'reply', FALSE, FALSE, NULL, NULL);

-- Insert sample knowledge articles
INSERT INTO knowledge_articles (article_id, title, content, summary, category_id, author_id, status, tags, keywords) VALUES
('KB_001', 'How to Reset Your Password', 'To reset your password: 1. Go to the login page 2. Click "Forgot Password" 3. Enter your email address 4. Check your email for reset link 5. Follow the instructions in the email', 'Step-by-step guide for password reset', 3, 2, 'published', ARRAY['password', 'reset', 'login'], ARRAY['password', 'reset', 'login', 'authentication']),
('KB_002', 'API Rate Limiting Guidelines', 'Our API implements rate limiting to ensure fair usage: - Standard tier: 1000 requests/hour - Premium tier: 5000 requests/hour - Enterprise tier: 20000 requests/hour. When you exceed limits, you will receive a 429 status code.', 'Understanding API rate limits and tiers', 1, 1, 'published', ARRAY['api', 'rate-limiting', 'limits'], ARRAY['api', 'rate', 'limit', 'requests', '429']),
('KB_003', 'Billing Cycle and Invoice Information', 'Your billing cycle starts on the day you first subscribed. Invoices are generated automatically and sent via email. You can download invoices from your account dashboard under Billing > Invoice History.', 'Information about billing cycles and invoices', 2, 3, 'published', ARRAY['billing', 'invoice', 'cycle'], ARRAY['billing', 'invoice', 'cycle', 'payment', 'subscription']);

-- Insert sample query interactions for AI learning
INSERT INTO query_interactions (query_id, customer_id, ticket_id, query_text, query_type, detected_language, detected_intent, sentiment, sentiment_score, urgency_level, urgency_score, category_prediction, category_confidence, response_text, response_type, processing_time_ms, total_processing_time_ms, agents_used, customer_satisfaction) VALUES
('QUERY_001', 'CUST_001', 'TKT_001', 'Our API is returning 500 errors for the users endpoint', 'complaint', 'en', 'technical_issue', 'negative', 0.75, 'high', 0.85, 'Technical Issues', 0.92, 'I understand this is a serious production issue. Let me immediately escalate this to our technical team.', 'escalation', 250, 1200, ARRAY['query_agent', 'knowledge_agent'], 5),
('QUERY_002', 'CUST_002', 'TKT_002', 'I was charged but my upgrade failed', 'complaint', 'en', 'billing_issue', 'negative', 0.68, 'medium', 0.65, 'Billing & Payments', 0.88, 'I can help resolve this billing discrepancy. Let me check your account details.', 'direct_answer', 320, 980, ARRAY['query_agent', 'response_agent'], 4),
('QUERY_003', 'CUST_003', 'TKT_003', 'Cannot login to my account', 'request', 'en', 'account_access', 'neutral', 0.45, 'medium', 0.60, 'Account Management', 0.85, 'Login issues can be frustrating. Let me help you regain access to your account.', 'direct_answer', 280, 850, ARRAY['query_agent'], 5);

-- Insert sample customer feedback
INSERT INTO customer_feedback (feedback_id, customer_id, ticket_id, query_id, feedback_type, rating, comment, tags) VALUES
('FB_001', 'CUST_001', 'TKT_001', 'QUERY_001', 'satisfaction', 5, 'Excellent technical support. The issue was resolved quickly and the communication was clear throughout the process.', ARRAY['excellent', 'technical', 'quick']),
('FB_002', 'CUST_002', 'TKT_002', 'QUERY_002', 'satisfaction', 4, 'Good resolution of the billing issue. Could have been faster but the agent was helpful.', ARRAY['good', 'billing', 'helpful']),
('FB_003', 'CUST_003', 'TKT_003', 'QUERY_003', 'satisfaction', 5, 'Very quick resolution of my login problem. Thank you!', ARRAY['quick', 'login', 'resolved']);

-- Insert AI agent performance data
INSERT INTO agent_performance (agent_id, agent_type, generation, fitness_score, genes, performance_metrics, queries_processed) VALUES
('query_agent_v1', 'query', 1, 0.8750, '{"response_speed": 0.85, "accuracy": 0.90, "empathy": 0.80}', '{"success_rate": 0.87, "avg_response_time": 280, "customer_satisfaction": 4.2}', 150),
('knowledge_agent_v1', 'knowledge', 1, 0.8200, '{"search_accuracy": 0.88, "relevance": 0.85, "coverage": 0.75}', '{"success_rate": 0.82, "avg_response_time": 450, "customer_satisfaction": 4.0}', 98),
('response_agent_v1', 'response', 1, 0.9100, '{"clarity": 0.92, "completeness": 0.90, "tone": 0.88}', '{"success_rate": 0.91, "avg_response_time": 200, "customer_satisfaction": 4.5}', 203);

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

-- Log successful initialization
INSERT INTO customer_feedback (feedback_id, customer_id, feedback_type, rating, comment, tags) VALUES
('INIT_SUCCESS', 'SYSTEM', 'system', 5, 'Database schema and sample data initialized successfully. All tables, indexes, triggers, and views created. Sample data inserted for testing and demonstration purposes.', ARRAY['initialization', 'success', 'schema', 'sample-data']);
