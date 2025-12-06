# BLB3D System Diagrams (Mermaid)

These diagrams render automatically in VS Code with the Mermaid extension, or view at https://mermaid.live

---

## 1. High-Level System Architecture

```mermaid
flowchart TB
    subgraph Sales["Sales Channels"]
        SQ[Squarespace<br/>B2C Retail]
        QP[Quote Portal<br/>B2B Custom]
        WC[WooCommerce<br/>Future]
    end

    subgraph Core["Core System"]
        ERP[ERP Backend<br/>FastAPI :8000]
        ML[ML Dashboard<br/>FastAPI :8001]
        DB[(SQL Server<br/>Express)]
    end

    subgraph External["External Services"]
        ST[Stripe<br/>Payments]
        EP[EasyPost<br/>Shipping]
        EM[Email<br/>Notifications]
    end

    subgraph Production["Print Farm"]
        BS[BambuStudio<br/>CLI]
        subgraph Printers["Printer Fleet"]
            P1[Donatello<br/>A1]
            P2[Leonardo<br/>P1S]
            P3[Michelangelo<br/>A1]
            P4[Raphael<br/>A1]
        end
    end

    SQ --> ERP
    QP --> ERP
    WC --> ERP
    
    ERP <--> DB
    ERP <--> ML
    ERP <--> ST
    ERP <--> EP
    ERP --> EM
    
    ML --> BS
    BS --> Printers
```

---

## 2. Quote Generation Flow

```mermaid
sequenceDiagram
    participant C as Customer
    participant QP as Quote Portal<br/>(React)
    participant ERP as ERP Backend<br/>(:8000)
    participant ML as ML Dashboard<br/>(:8001)
    participant BS as BambuStudio<br/>CLI

    C->>QP: Upload 3MF + Select Options
    QP->>ERP: POST /api/quotes/generate
    ERP->>ML: POST /api/quotes/generate
    ML->>BS: Slice with profiles
    BS-->>ML: G-code output
    ML->>ML: Analyze G-code<br/>(time, material, weight)
    ML->>ML: Calculate pricing
    ML-->>ERP: Quote data
    ERP->>ERP: Save to database
    ERP-->>QP: Quote response
    QP-->>C: Display quote + 3D preview
```

---

## 3. Payment Flow

```mermaid
flowchart TB
    subgraph Quote["Quote Display"]
        QR[Quote Result Page]
        SA[Enter Shipping Address]
        GR[Get Shipping Rates]
        SR[Select Rate]
    end

    subgraph Decision["Auto-Approve Check"]
        CHK{Has Notes?<br/>Price > $X?}
    end

    subgraph AutoApprove["Auto-Approved Path"]
        PAY[Pay Now Button]
        STRIPE[Stripe Checkout]
        SUCCESS[Payment Success]
    end

    subgraph Review["Review Path"]
        EMAIL[Enter Email]
        SUBMIT[Submit for Review]
        PENDING[Pending Review]
        ENG[Engineer Reviews]
        LINK[Send Payment Link]
    end

    subgraph Order["Order Creation"]
        SO[Create Sales Order]
        PROD[Create Product/BOM]
        PO[Create Prod Order]
    end

    QR --> SA --> GR --> SR --> CHK
    
    CHK -->|No| PAY
    CHK -->|Yes| EMAIL
    
    PAY --> STRIPE --> SUCCESS
    EMAIL --> SUBMIT --> PENDING --> ENG --> LINK --> STRIPE
    
    SUCCESS --> SO --> PROD --> PO
```

---

## 4. Data Model (Simplified)

```mermaid
erDiagram
    CUSTOMERS ||--o{ QUOTES : has
    CUSTOMERS ||--o{ SALES_ORDERS : places
    QUOTES ||--o| SALES_ORDERS : converts_to
    SALES_ORDERS ||--|{ ORDER_LINES : contains
    PRODUCTS ||--o{ ORDER_LINES : referenced_in
    PRODUCTS ||--o| BOMS : has
    BOMS ||--|{ BOM_ITEMS : contains
    MATERIAL_CATALOG ||--o{ BOM_ITEMS : used_in
    MATERIAL_CATALOG ||--o{ INVENTORY : tracked_in
    SALES_ORDERS ||--o{ PRODUCTION_ORDERS : generates
    PRODUCTION_ORDERS ||--o{ PRINT_JOBS : creates
    PRINTERS ||--o{ PRINT_JOBS : executes

    CUSTOMERS {
        int id PK
        string customer_number
        string name
        string email
    }
    
    QUOTES {
        int id PK
        string quote_number
        int customer_id FK
        string status
        decimal total_price
        string material
        string color
        int infill_percent
    }
    
    SALES_ORDERS {
        int id PK
        string order_number
        int customer_id FK
        int quote_id FK
        string status
        decimal total_amount
    }
    
    PRODUCTS {
        int id PK
        string sku
        string name
        decimal price
    }
    
    MATERIAL_CATALOG {
        int id PK
        string sku
        string material_type
        string color_name
        decimal price_per_kg
    }
```

---

## 5. Quote Status State Machine

```mermaid
stateDiagram-v2
    [*] --> Draft: Created
    Draft --> Approved: Auto-approve<br/>(no notes, price OK)
    Draft --> Pending: Needs review<br/>(has notes or high price)
    
    Pending --> PendingReview: Customer submits<br/>with email
    PendingReview --> Approved: Engineer approves
    PendingReview --> Rejected: Cannot fulfill
    
    Approved --> Accepted: Customer pays
    Approved --> Expired: 7 days timeout
    
    Pending --> Expired: 7 days timeout
    
    Accepted --> Converted: Order created
    Converted --> [*]
    Expired --> [*]
    Rejected --> [*]
```

---

## 6. Repository Structure

```mermaid
flowchart LR
    subgraph R1["blb3d-erp<br/>(GitHub: blb3d-print-farm)"]
        ERP_API[FastAPI Backend<br/>:8000]
        ERP_DB[Database Models]
        ERP_SVC[Services]
    end

    subgraph R2["bambu-print-suite"]
        ML_API[ML Dashboard<br/>:8001]
        QE[Quote Engine]
        SLICER[BambuStudio<br/>Integration]
    end

    subgraph R3["quote-portal"]
        REACT[React Frontend<br/>:5173]
        VIEWER[3D Viewer<br/>Three.js]
    end

    REACT --> ERP_API
    ERP_API --> ML_API
    ML_API --> SLICER
    ERP_API --> ERP_DB
```

---

## 7. Tech Stack Overview

```mermaid
mindmap
    root((BLB3D<br/>Print Farm))
        Frontend
            React
            Vite
            Three.js
            Tailwind CSS
        Backend
            FastAPI
            SQLAlchemy
            Pydantic
            Python 3.11
        Database
            SQL Server Express
            20+ Tables
        Integrations
            Stripe
            EasyPost
            BambuStudio CLI
            MQTT
        Infrastructure
            GitHub
            Local Server
            Printer Fleet
```

---

## 8. Complete System Flow

```mermaid
flowchart TB
    subgraph Customer["Customer Journey"]
        C1[Upload 3MF]
        C2[Select Options]
        C3[View Quote]
        C4[Enter Shipping]
        C5[Pay or Submit]
    end

    subgraph Backend["Backend Processing"]
        B1[Receive File]
        B2[Call ML Dashboard]
        B3[Slice Model]
        B4[Calculate Price]
        B5[Save Quote]
        B6[Process Payment]
    end

    subgraph Production["Production"]
        P1[Create Order]
        P2[Create Prod Order]
        P3[Assign Printer]
        P4[Print Job]
        P5[Quality Check]
    end

    subgraph Fulfillment["Fulfillment"]
        F1[Pack Order]
        F2[Create Label]
        F3[Ship]
        F4[Track]
    end

    C1 --> B1 --> B2 --> B3 --> B4 --> B5
    B5 --> C3 --> C4 --> C5 --> B6
    B6 --> P1 --> P2 --> P3 --> P4 --> P5
    P5 --> F1 --> F2 --> F3 --> F4
```

---

## VS Code Setup

Install the **Markdown Preview Mermaid Support** extension:
1. Open Extensions (Ctrl+Shift+X)
2. Search for "Markdown Preview Mermaid Support"
3. Install by Matt Bierner
4. Open this file and press Ctrl+Shift+V to preview

Or use **Mermaid Preview** extension for side-by-side editing.
