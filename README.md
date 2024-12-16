# MLOps Platform Technical Assessment

## Overview
This technical assessment evaluates your backend development skills through implementing a cluster management system. The boilerplate provides a foundation with TODO markers for key functionality, allowing you to demonstrate your understanding of:
- Session-based authentication and user management
- Organization management with invite system
- Resource allocation and scheduling algorithms
- API design and implementation

## Tech Stack
- Python 3.11
- FastAPI web framework
- SQLAlchemy ORM
- PostgreSQL database
- Pydantic for data validation
- Pytest for testing
- Session-based authentication
- Role-Based Access Control (RBAC)

## Time Limit
You have 4-5 hours to complete this assessment. Focus on core functionality first:
1. Authentication system
2. Organization management
3. Basic cluster operations
4. Simple deployment scheduling

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

# Session Configuration
SECRET_KEY=your-secret-key  # Used for session encryption
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
- [ ] Implement session-based authentication (login/logout)
- [ ] Complete user registration with password hashing
- [ ] Add organization creation with random invite codes
- [ ] Implement organization join functionality via invite codes

### 2. Cluster Management
- [ ] Create clusters with resource limits (CPU, RAM, GPU)
- [ ] Track available resources
- [ ] List clusters for organization members
- [ ] Validate resource availability

### 3. Deployment Management
- [ ] Create deployments with resource requirements
- [ ] Implement basic scheduling algorithm
- [ ] Track deployment status
- [ ] Handle resource allocation/deallocation

### 4. Advanced Features (Optional)
- [ ] Add Role-Based Access Control (RBAC)
- [ ] Implement rate limiting
- [ ] Add comprehensive test coverage
- [ ] Enhance API documentation

## Evaluation Criteria
1. **Code Quality (40%)**
   - Clean, readable, and well-organized code
   - Proper error handling
   - Effective use of FastAPI features
   - Type hints and validation

2. **System Design (30%)**
   - Authentication implementation
   - Resource management approach
   - Scheduling algorithm design
   - API structure and organization

3. **Functionality (20%)**
   - Working authentication system
   - Proper resource tracking
   - Successful deployment scheduling
   - Correct error responses

4. **Testing & Documentation (10%)**
   - Test coverage
   - API documentation
   - Code comments
   - README updates

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
