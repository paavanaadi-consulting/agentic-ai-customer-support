# Setup Guide

## Prerequisites
- Python 3.8+
- PostgreSQL
- Qdrant
- Kafka (optional, for event streaming)

## Installation
1. Clone the repository.
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set up your `.env` file (see `.env.example`).
4. Initialize the database:
   ```sh
   python scripts/init_db.py
   ```
5. (Optional) Seed the database:
   ```sh
   python scripts/seed_db.py
   ```
6. Start the API server:
   ```sh
   python main.py --mode server
   ```

## Additional Scripts
- See the `scripts/` folder for import/export, health checks, and more.
