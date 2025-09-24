# Civic Eye - AI-Powered Smart Civic Reporting Platform

## Overview

Civic Eye is an AI-augmented civic issue reporting platform that enables citizens to report community problems through multiple channels (images, text, voice) while leveraging artificial intelligence for automated classification, fake report detection, and complaint generation. The system connects citizens with municipal authorities through a transparent, efficient reporting workflow.

The platform addresses the critical need for responsive civic governance by automating issue detection, reducing manual processing overhead, and providing real-time tracking capabilities. Citizens can submit reports which are automatically categorized, validated, and routed to appropriate authorities based on AI analysis.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The application uses a traditional server-side rendered architecture with Flask templates and modern CSS/JavaScript for enhanced user experience. The frontend consists of responsive HTML pages with Bootstrap-style components, featuring a clean dashboard interface for citizens and an administrative panel for authorities. JavaScript modules handle client-side functionality including geolocation services, file uploads, and Google Maps integration.

### Backend Architecture
Built on Flask as the primary web framework, the backend follows a modular architecture with distinct separation of concerns:

- **Application Layer**: Flask routes handle HTTP requests and responses, with JWT-based authentication for session management
- **Service Layer**: Specialized AI modules for image classification, NLP analysis, fake detection, and complaint generation
- **Data Layer**: MongoDB integration for persistent storage with fallback mechanisms when database is unavailable

The backend implements a pluggable AI architecture where each AI component (image classification, NLP, fake detection) can operate independently and gracefully degrade when external AI services are unavailable.

### Data Storage Solutions
MongoDB serves as the primary database for storing reports, user accounts, and authority information. The system includes comprehensive indexing strategies for performance optimization and implements automatic seeding of default authorities and admin accounts. A fallback mechanism ensures basic functionality when database connectivity is compromised.

Data models include:
- **ReportRecord**: Complete civic issue reports with metadata, location, and processing status
- **User Management**: Role-based access control with citizen and admin user types
- **Authority Mapping**: Automatic routing of issues to appropriate municipal departments

### Authentication and Authorization
JWT-based authentication provides stateless session management with configurable token expiration. The system implements role-based access control distinguishing between citizen users and administrative accounts. Password security uses bcrypt hashing for credential protection.

### AI/ML Integration Architecture
The platform implements a hybrid AI approach combining multiple machine learning techniques:

**Image Classification**: Uses Hugging Face transformers with vision models (ViT) for automated issue type detection from uploaded images. Includes comprehensive label mapping to translate generic model outputs into civic issue categories.

**Natural Language Processing**: Implements zero-shot classification using BART models for text analysis, with keyword-based fallback for robust operation. Supports multilingual content including Hindi keywords for broader accessibility.

**Fake Report Detection**: Combines TF-IDF text similarity analysis with geospatial proximity detection to identify duplicate or suspicious reports. Uses configurable thresholds for similarity scoring and temporal pattern analysis.

**Complaint Generation**: Template-based formal complaint generation with issue-specific customization and priority statements for different civic problems.

All AI components include graceful degradation mechanisms, operating with reduced functionality when external ML libraries or models are unavailable.

## External Dependencies

### Core Web Framework
- **Flask**: Primary web application framework with CORS support for API endpoints
- **Flask-JWT-Extended**: JWT token management for stateless authentication
- **Werkzeug**: File upload handling and security utilities

### Database Integration
- **PyMongo**: MongoDB driver with connection pooling and error handling
- **MongoDB Atlas**: Cloud database service (configurable via environment variables)

### AI/ML Stack
- **Hugging Face Transformers**: Pre-trained models for image classification and NLP tasks
- **PyTorch**: Deep learning framework for model inference
- **Scikit-learn**: Traditional ML algorithms for similarity analysis and clustering
- **Pillow**: Image processing and manipulation
- **NumPy**: Numerical computing for vector operations

### Frontend Enhancement
- **Google Maps JavaScript API**: Interactive mapping and geolocation services
- **Font Awesome**: Icon library for enhanced UI components
- **Custom CSS/JavaScript**: Responsive design and client-side functionality

### Security and Utilities
- **Passlib**: Password hashing with bcrypt for secure credential storage
- **Python-dotenv**: Environment variable management for configuration
- **UUID**: Unique identifier generation for reports and sessions

### Development and Deployment
- **Python 3.8+**: Core runtime environment
- **pip**: Package management with requirements.txt specification
- **Environment Variables**: Configurable deployment through .env files

The system is designed to function with varying levels of external service availability, providing core functionality even when advanced AI features are temporarily unavailable.