# TrustViz System Architecture

This document outlines the high-level, service-oriented architecture for the TrustViz platform.

## Architecture Diagramj

```mermaid
graph TD
    subgraph External Systems
        ECommerce["E-commerce Platforms (Data Source)"]
    end

    subgraph TrustViz System
        APIGateway["API Gateway"]
        MessageBus["Message Bus (e.g., RabbitMQ/Kafka)"]

        subgraph Core Services
            DataIngestion["Data Ingestion Service"]
            SwarmIntelligence["Swarm Intelligence Core"]
            PerceptualAI["Perceptual AI Service"]
            TrustLedger["Trust Ledger Service"]
        end

        subgraph Data Stores
            LedgerDB["(Blockchain) Trust Ledger DB"]
            ModelRegistry["AI Model Registry"]
        end
    end

    subgraph Consumers
        Frontend["Frontend/Dashboard"]
        ThirdParty["3rd Party Integrations"]
    end

    ECommerce --> DataIngestion
    DataIngestion -- "Raw Data (Listings, Sellers)" --> MessageBus
    MessageBus -- "Events" --> SwarmIntelligence
    SwarmIntelligence -- "Image Analysis Request" --> MessageBus
    MessageBus -- "Request" --> PerceptualAI
    PerceptualAI -- "Counterfeit Score" --> MessageBus
    MessageBus -- "Score" --> SwarmIntelligence
    SwarmIntelligence -- "Update Reputation" --> MessageBus
    MessageBus -- "Transaction" --> TrustLedger
    PerceptualAI --> ModelRegistry
    TrustLedger --> LedgerDB

    APIGateway --> DataIngestion
    APIGateway --> SwarmIntelligence
    APIGateway --> TrustLedger

    Frontend --> APIGateway
    ThirdParty --> APIGateway
```

## Component Descriptions

*   **Data Ingestion Service:** Responsible for collecting data from e-commerce platforms via APIs or other means. It publishes raw data to the Message Bus.
*   **Swarm Intelligence Core:** A network of decentralized agents that subscribe to data events from the Message Bus. These agents perform initial analysis, coordinate tasks, and decide when to invoke the Perceptual AI or update the Trust Ledger.
*   **Perceptual AI Service:** A specialized service that exposes an API for visual counterfeit detection. It will receive image data, process it using Vision Transformers and other models, and return a confidence score.
*   **Trust Ledger Service:** Manages the immutable reputation ledger. It provides an API to record reputation events (transactions) and query seller trust scores.
*   **API Gateway:** A single entry point for all external-facing communication, routing requests to the appropriate internal services.
*   **Message Bus:** The central nervous system for asynchronous communication between services, ensuring loose coupling and resilience.