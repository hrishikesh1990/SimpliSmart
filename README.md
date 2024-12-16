# Hypervisor-like Service for MLOps Platform

## Overview
This is a FastAPI technical assessment boilerplate designed to evaluate backend system design, scalability, and software engineering skills. The project implements a cluster management system with user authentication, organization management, and deployment scheduling.

## Tech Stack
- Python 3.11
- FastAPI web framework
- SQLAlchemy ORM
- PostgreSQL database
- Pydantic for data validation
- Pytest for testing
- JWT authentication
- Role-Based Access Control (RBAC)

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL database

### Setup Instructions
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# JWT Configuration
SECRET_KEY=your-secret-key
```

3. Run the application:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

4. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Assessment Tasks

### 1. User Authentication and Organization Management
- [ ] Implement JWT token creation and validation
- [ ] Complete user registration and login endpoints
- [ ] Implement organization creation with invite codes
- [ ] Add organization join functionality

### 2. Cluster Management
- [ ] Implement cluster creation with resource limits
- [ ] Add resource tracking functionality
- [ ] Implement cluster listing for organization members

### 3. Deployment Management
- [ ] Implement deployment creation endpoint
- [ ] Add resource allocation logic
- [ ] Implement deployment queue system
- [ ] Create scheduling algorithm based on priority and resources

### 4. Advanced Features
- [ ] Implement Role-Based Access Control (RBAC)
- [ ] Add rate limiting
- [ ] Implement comprehensive test coverage
- [ ] Add API documentation

## Project Structure
```
.
├── app
│   ├── api
│   │   └── v1
│   │       ├── endpoints
│   │       │   ├── auth.py
│   │       │   ├── clusters.py
│   │       │   ├── deployments.py
│   │       │   └── organizations.py
│   │       └── api.py
│   ├── core
│   │   ├── config.py
│   │   ├── deps.py
│   │   └── security.py
│   ├── db
│   │   ├── base.py
│   │   └── session.py
│   ├── models
│   │   ├── cluster.py
│   │   ├── deployment.py
│   │   ├── organization.py
│   │   └── user.py
│   ├── schemas
│   │   ├── cluster.py
│   │   ├── deployment.py
│   │   ├── organization.py
│   │   └── user.py
│   └── main.py
└── tests
    ├── conftest.py
    └── test_api
```

## API Documentation
The API documentation is available through Swagger UI and ReDoc:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Testing
Run the tests using pytest:
```bash
pytest
```

## Evaluation Criteria
1. Code quality and organization
2. System design decisions
3. Implementation of required features
4. Test coverage and quality
5. Documentation and code comments
6. Bonus features implementation
