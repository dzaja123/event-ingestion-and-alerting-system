# IoT Event Ingestion System

Backend system for processing IoT sensor events and generating alerts.

## Overview

Building a microservices architecture to handle real-time IoT data ingestion and alerting for various sensor types.

### Planned Components

- **Ingestion Service**: FastAPI service to receive and validate IoT events
- **Alerting Service**: Process events and generate alerts based on business rules
- **Database**: PostgreSQL for data persistence
- **Message Queue**: RabbitMQ for event streaming between services
- **Cache**: Redis for performance optimization

## Sensor Types

- Access control sensors (MAC validation)
- Radar speed sensors 
- Motion detection cameras

## Alert Rules (Draft)

1. Unauthorized access attempts
2. Speed violations >90 km/h
3. Motion in restricted areas after hours

## Development Setup

Requirements:
- Python 3.11+
- PostgreSQL
- Redis
- RabbitMQ
- Docker

## Project Structure

```
├── ingestion_service/
├── alerting_service/
└── docker-compose.yml
```