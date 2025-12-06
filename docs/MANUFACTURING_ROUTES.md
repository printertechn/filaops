# Manufacturing Routes - Design Document

## Overview

Manufacturing Routes separate **what goes into a product** (BOM) from **how it's made** (Routing).

This enables:
- **Capacity Planning** - Can we fulfill this order by Friday?
- **Scheduling** - Which printer should run which job?
- **Costing** - Labor + machine time costs separate from materials
- **Bottleneck Detection** - Where's the constraint?

## Data Model

### Work Centers

A work center is where work happens. Can be:
- **Machine Pool** - Group of interchangeable machines (10 FDM printers)
- **Work Station** - Physical location (QC bench, assembly table)
- **Labor Pool** - People doing work (packers, assemblers)

```sql
CREATE TABLE work_centers (
    id INT IDENTITY(1,1) PRIMARY KEY,
    code NVARCHAR(50) NOT NULL UNIQUE,      -- 'FDM-POOL', 'QC-STATION', 'ASSEMBLY'
    name NVARCHAR(200) NOT NULL,            -- 'FDM Printer Pool'
    description NVARCHAR(MAX),

    -- Type
    center_type NVARCHAR(50) NOT NULL,      -- 'machine', 'station', 'labor'

    -- Capacity (per day by default)
    capacity_hours_per_day DECIMAL(10,2),   -- 20 hrs (allows overnight)
    capacity_units_per_hour DECIMAL(10,2),  -- Alternative: 5 units/hr for assembly

    -- Costing
    machine_rate_per_hour DECIMAL(18,4),    -- $/hr for machine time
    labor_rate_per_hour DECIMAL(18,4),      -- $/hr for labor
    overhead_rate_per_hour DECIMAL(18,4),   -- $/hr for overhead

    -- Scheduling
    is_bottleneck BIT DEFAULT 0,            -- Flag for constraint resource
    scheduling_priority INT DEFAULT 50,      -- Higher = schedule first

    -- Status
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
```

### Resources (Individual Machines)

Optional - for when you need to track individual machines within a pool.

```sql
CREATE TABLE resources (
    id INT IDENTITY(1,1) PRIMARY KEY,
    work_center_id INT NOT NULL REFERENCES work_centers(id),
    code NVARCHAR(50) NOT NULL,             -- 'P1-S-001' (Printer 1)
    name NVARCHAR(200) NOT NULL,            -- 'X1C #1 - Front Left'

    -- Machine details
    machine_type NVARCHAR(100),             -- 'X1C', 'P1S', 'A1'
    serial_number NVARCHAR(100),

    -- Bambu Integration
    bambu_device_id NVARCHAR(100),          -- Links to Bambu Print Suite
    bambu_ip_address NVARCHAR(50),

    -- Capacity override (if different from work center default)
    capacity_hours_per_day DECIMAL(10,2),

    -- Status
    status NVARCHAR(50) DEFAULT 'available', -- 'available', 'busy', 'maintenance', 'offline'
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
```

### Routings

A routing defines HOW to make a product - the sequence of operations.

```sql
CREATE TABLE routings (
    id INT IDENTITY(1,1) PRIMARY KEY,
    product_id INT NOT NULL REFERENCES products(id),
    code NVARCHAR(50) NOT NULL,             -- 'RTG-WIDGET-001'
    name NVARCHAR(200),                     -- 'Widget Standard Routing'

    -- Version control (like BOMs)
    version INT DEFAULT 1,
    revision NVARCHAR(20) DEFAULT '1.0',
    is_active BIT DEFAULT 1,

    -- Calculated totals (updated when operations change)
    total_setup_time_minutes DECIMAL(10,2),
    total_run_time_minutes DECIMAL(10,2),
    total_cost DECIMAL(18,4),

    -- Dates
    effective_date DATE,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),

    CONSTRAINT UQ_routing_product_version UNIQUE (product_id, version)
);
```

### Routing Operations (Steps)

Each step in the manufacturing process.

```sql
CREATE TABLE routing_operations (
    id INT IDENTITY(1,1) PRIMARY KEY,
    routing_id INT NOT NULL REFERENCES routings(id) ON DELETE CASCADE,
    work_center_id INT NOT NULL REFERENCES work_centers(id),

    -- Sequence
    sequence INT NOT NULL,                  -- 10, 20, 30 (gaps for insertions)
    operation_code NVARCHAR(50),            -- 'PRINT', 'QC', 'ASSEMBLE', 'PACK'
    operation_name NVARCHAR(200),           -- 'FDM Print'
    description NVARCHAR(MAX),

    -- Time (in minutes)
    setup_time_minutes DECIMAL(10,2) DEFAULT 0,  -- Per batch setup
    run_time_minutes DECIMAL(10,2) NOT NULL,     -- Per unit production time
    wait_time_minutes DECIMAL(10,2) DEFAULT 0,   -- Cooling, curing, etc.
    move_time_minutes DECIMAL(10,2) DEFAULT 0,   -- Transport to next station

    -- For 3D printing: runtime can come from slicer
    runtime_source NVARCHAR(50) DEFAULT 'manual', -- 'manual', 'slicer', 'calculated'
    slicer_file_path NVARCHAR(500),              -- Link to 3MF/gcode for time estimate

    -- Quantity
    units_per_cycle INT DEFAULT 1,          -- How many made per run (batch size on print bed)
    scrap_rate_percent DECIMAL(5,2) DEFAULT 0,

    -- Costing (override work center rates if needed)
    labor_rate_override DECIMAL(18,4),
    machine_rate_override DECIMAL(18,4),

    -- Dependencies
    predecessor_operation_id INT,           -- Must complete before this starts
    can_overlap BIT DEFAULT 0,              -- Can start before predecessor finishes?

    -- Status
    is_active BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE()
);
```

## Example: Widget Product

### BOM (What goes in)
| Component | Qty | Unit |
|-----------|-----|------|
| PLA Black | 45 | g |
| M3x8 Screw | 4 | EA |
| Widget Base (printed) | 1 | EA |
| Widget Cover (printed) | 1 | EA |

### Routing (How it's made)
| Seq | Operation | Work Center | Setup | Run Time | Notes |
|-----|-----------|-------------|-------|----------|-------|
| 10 | Print Base | FDM Pool | 5 min | 2.5 hrs | From slicer |
| 20 | Print Cover | FDM Pool | 5 min | 1.5 hrs | From slicer |
| 30 | QC Inspect | QC Station | 0 | 5 min | Visual check |
| 40 | Assembly | Assembly | 0 | 10 min | Insert screws |
| 50 | Final QC | QC Station | 0 | 2 min | Function test |
| 60 | Pack | Shipping | 0 | 3 min | Box & label |

**Total Time:** ~4.5 hours (mostly print time)
**Bottleneck:** FDM Pool (print time dominates)

## Work Center Types for 3D Print Farm

### 1. FDM Printer Pool
- **Machines:** 10 printers (X1C, P1S, A1)
- **Capacity:** 200 printer-hours/day (10 × 20 hrs)
- **Rate:** $2/hr machine time
- **Key Metric:** Print hours utilization

### 2. Quality Control
- **Type:** Station
- **Capacity:** 8 hrs/day (1 person)
- **Rate:** $25/hr labor
- **Operations:** Visual inspect, dimension check, function test

### 3. Assembly
- **Type:** Station
- **Capacity:** 8 hrs/day
- **Rate:** $20/hr labor
- **Operations:** Insert hardware, combine printed parts

### 4. Packing/Shipping
- **Type:** Station
- **Capacity:** 8 hrs/day
- **Rate:** $18/hr labor
- **Operations:** Box, label, ship

## Bambu Print Suite Integration

The magic happens here:

1. **Print Time from Slicer**
   - When a 3MF is sliced, Bambu Studio/Print Suite knows the exact print time
   - We pull this into `routing_operations.run_time_minutes`
   - No manual time entry needed for print operations

2. **Printer Status**
   - `resources.status` syncs with Bambu Print Suite
   - Know which printers are available, busy, or offline

3. **Job Assignment**
   - When scheduling a production order, assign to specific printer
   - Print Suite sends the job to that printer
   - Track actual vs estimated time

## Capacity Calculation

### Daily Capacity Example

**FDM Pool:**
- 10 printers × 20 hrs = 200 printer-hours available
- Jobs scheduled today = 180 printer-hours
- Remaining capacity = 20 hrs (10%)

**Assembly:**
- 8 hours available
- Jobs scheduled = 6 hours
- Remaining = 2 hours (25%)

### Can We Make 50 Widgets This Week?

Widget Routing Total: 4.5 hrs (4 hrs print + 0.5 hrs labor)

**Print Capacity:**
- Need: 50 × 4 hrs = 200 print-hours
- Available: 200 hrs/day × 5 days = 1000 hrs
- ✅ Plenty of print capacity

**Assembly Capacity:**
- Need: 50 × 0.5 hrs = 25 labor-hours
- Available: 8 hrs/day × 5 days = 40 hrs
- ✅ Enough, but tighter

**Bottleneck:** Assembly would fill up faster than printing.

## API Endpoints

```
# Work Centers
GET    /api/v1/work-centers
POST   /api/v1/work-centers
GET    /api/v1/work-centers/{id}
PUT    /api/v1/work-centers/{id}
GET    /api/v1/work-centers/{id}/capacity  # Current load

# Resources (Machines)
GET    /api/v1/work-centers/{id}/resources
POST   /api/v1/work-centers/{id}/resources
GET    /api/v1/resources/{id}
PUT    /api/v1/resources/{id}
PATCH  /api/v1/resources/{id}/status

# Routings
GET    /api/v1/routings
POST   /api/v1/routings
GET    /api/v1/routings/{id}
PUT    /api/v1/routings/{id}
GET    /api/v1/products/{id}/routing  # Get active routing for product

# Routing Operations
GET    /api/v1/routings/{id}/operations
POST   /api/v1/routings/{id}/operations
PUT    /api/v1/routing-operations/{id}
DELETE /api/v1/routing-operations/{id}

# Capacity Planning
GET    /api/v1/capacity/summary              # All work centers
GET    /api/v1/capacity/work-center/{id}     # Specific work center
POST   /api/v1/capacity/check                # Can we make X by date Y?
```

## UI Screens

### 1. Work Centers List
- Table of all work centers
- Capacity utilization bars (today/this week)
- Quick status (available capacity)

### 2. Work Center Detail
- Edit properties
- List of resources (machines)
- Capacity calendar view
- Current jobs in progress

### 3. Routing Editor
- Select product
- Drag-drop operation sequence
- Set times (or pull from slicer)
- Calculate total time/cost

### 4. Capacity Dashboard
- Overview of all work centers
- Bottleneck highlighting
- Week/month forward view

## Next Steps

1. **Create Tables** - work_centers, resources, routings, routing_operations
2. **Build Work Center CRUD** - API + UI
3. **Build Routing Editor** - API + UI
4. **Integrate with Bambu Print Suite** - Pull print times, sync status
5. **Production Order Scheduling** - Use routings to schedule work
