# Agents Overview

## QueryAgent
- Analyzes and classifies customer queries.
- Extracts intent, sentiment, urgency, and category.

## KnowledgeAgent
- Retrieves relevant knowledge base articles or documents.
- Uses semantic search and metadata filtering.

## ResponseAgent
- Generates and formats responses for customers.
- Personalizes tone, length, and content.

## Extending Agents
- All agents inherit from a common base class.
- Add new agent types by subclassing and implementing `process_input` and `set_chromosome`.
