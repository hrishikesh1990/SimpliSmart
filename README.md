# Technical Assessment: Cluster Management System

## Overview
This is a technical assessment for building a backend service that manages user authentication, organization membership, cluster resource allocation, and deployment scheduling.

## Key Features to Implement

### 1. User Authentication and Organization Management
- Implement JWT-based authentication
- User registration and login
- Organization creation and management
- Invite code system for organization joining

### 2. Role-Based Access Control (RBAC)
- Admin: Full system access
- Developer: Can create/manage deployments
- Viewer: Can only view resources

### 3. Cluster Management
- Create clusters with resource limits
- Track resource allocation
- Manage cluster access

### 4. Deployment System
- Create deployments using Docker images
- Resource allocation tracking
- Priority-based deployment scheduling
- Queue management for pending deployments

## Technical Requirements

### Prerequisites
- Python 3.11+
- PostgreSQL
- FastAPI
- SQLAlchemy

### Setup Instructions
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```
   DATABASE_URL=postgresql://user:password@localhost/dbname
   SECRET_KEY=your-secret-key
   ```

3. Initialize the database:
   ```bash
   # TODO: Add database initialization commands
   ```

4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

5. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Assessment Tasks

### 1. Authentication and Authorization
- [ ] Implement JWT token generation and validation
- [ ] Add role-based access control (Admin, Developer, Viewer)
- [ ] Create user registration and login endpoints

### 2. Organization Management
- [ ] Implement organization creation
- [ ] Add invite code generation and validation
- [ ] Create endpoints for joining organizations

### 3. Cluster Management
- [ ] Implement cluster creation with resource limits
- [ ] Add resource tracking functionality
- [ ] Create endpoints for cluster management

### 4. Deployment System
- [ ] Create deployment creation endpoints
- [ ] Implement resource allocation tracking
- [ ] Add priority-based scheduling
- [ ] Implement deployment queue management

### 5. Testing
- [ ] Write unit tests for core functionality
- [ ] Add integration tests for API endpoints
- [ ] Implement test coverage reporting

## Time Limit
- Expected completion time: 4-5 hours

## Evaluation Criteria
1. Code quality and organization
2. Implementation of required features
3. Test coverage and quality
4. API design and documentation
5. Error handling and edge cases
6. Documentation quality

## Bonus Points
- [ ] Advanced authentication features
- [ ] Comprehensive test coverage
- [ ] Documentation quality
- [ ] Code organization and modularity
- [ ] Performance optimizations
