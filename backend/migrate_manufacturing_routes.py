"""
Migration script to create manufacturing routes tables.

Creates:
- work_centers table (FDM Pool, QC Station, Assembly, Shipping)
- resources table (individual machines/printers)
- routings table (how to make a product)
- routing_operations table (steps in the routing)

Run from backend directory:
    python migrate_manufacturing_routes.py
"""

from app.db.session import engine
from sqlalchemy import text


def run_migration():
    print("=== Creating Manufacturing Routes Tables ===\n")

    with engine.connect() as conn:
        # =====================================================================
        # Create work_centers table
        # =====================================================================
        print("Creating work_centers table...")
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'work_centers')
            BEGIN
                CREATE TABLE work_centers (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    code NVARCHAR(50) NOT NULL UNIQUE,
                    name NVARCHAR(200) NOT NULL,
                    description NVARCHAR(MAX) NULL,

                    -- Type: 'machine', 'station', 'labor'
                    center_type NVARCHAR(50) NOT NULL DEFAULT 'station',

                    -- Capacity (per day)
                    capacity_hours_per_day DECIMAL(10,2) NULL,
                    capacity_units_per_hour DECIMAL(10,2) NULL,

                    -- Costing ($/hr)
                    machine_rate_per_hour DECIMAL(18,4) NULL,
                    labor_rate_per_hour DECIMAL(18,4) NULL,
                    overhead_rate_per_hour DECIMAL(18,4) NULL,

                    -- Scheduling
                    is_bottleneck BIT DEFAULT 0 NOT NULL,
                    scheduling_priority INT DEFAULT 50 NOT NULL,

                    -- Status
                    is_active BIT DEFAULT 1 NOT NULL,
                    created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                    updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE()
                );

                CREATE INDEX IX_work_centers_code ON work_centers(code);
                CREATE INDEX IX_work_centers_type ON work_centers(center_type);
                PRINT 'Created work_centers table';
            END
            ELSE
                PRINT 'work_centers table already exists';
        """))
        conn.commit()
        print("  work_centers table ready")

        # =====================================================================
        # Create resources table (individual machines)
        # =====================================================================
        print("Creating resources table...")
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'resources')
            BEGIN
                CREATE TABLE resources (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    work_center_id INT NOT NULL,
                    code NVARCHAR(50) NOT NULL,
                    name NVARCHAR(200) NOT NULL,

                    -- Machine details
                    machine_type NVARCHAR(100) NULL,
                    serial_number NVARCHAR(100) NULL,

                    -- Bambu Integration
                    bambu_device_id NVARCHAR(100) NULL,
                    bambu_ip_address NVARCHAR(50) NULL,

                    -- Capacity override
                    capacity_hours_per_day DECIMAL(10,2) NULL,

                    -- Status: 'available', 'busy', 'maintenance', 'offline'
                    status NVARCHAR(50) DEFAULT 'available' NOT NULL,
                    is_active BIT DEFAULT 1 NOT NULL,
                    created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                    updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

                    CONSTRAINT FK_resources_work_center FOREIGN KEY (work_center_id)
                        REFERENCES work_centers(id)
                );

                CREATE INDEX IX_resources_work_center ON resources(work_center_id);
                CREATE INDEX IX_resources_code ON resources(code);
                CREATE INDEX IX_resources_status ON resources(status);
                PRINT 'Created resources table';
            END
            ELSE
                PRINT 'resources table already exists';
        """))
        conn.commit()
        print("  resources table ready")

        # =====================================================================
        # Create routings table
        # =====================================================================
        print("Creating routings table...")
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'routings')
            BEGIN
                CREATE TABLE routings (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    product_id INT NOT NULL,
                    code NVARCHAR(50) NOT NULL,
                    name NVARCHAR(200) NULL,

                    -- Version control
                    version INT DEFAULT 1 NOT NULL,
                    revision NVARCHAR(20) DEFAULT '1.0' NOT NULL,
                    is_active BIT DEFAULT 1 NOT NULL,

                    -- Calculated totals
                    total_setup_time_minutes DECIMAL(10,2) NULL,
                    total_run_time_minutes DECIMAL(10,2) NULL,
                    total_cost DECIMAL(18,4) NULL,

                    -- Dates
                    effective_date DATE NULL,
                    notes NVARCHAR(MAX) NULL,
                    created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                    updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

                    CONSTRAINT FK_routings_product FOREIGN KEY (product_id)
                        REFERENCES products(id),
                    CONSTRAINT UQ_routing_product_version UNIQUE (product_id, version)
                );

                CREATE INDEX IX_routings_product ON routings(product_id);
                CREATE INDEX IX_routings_code ON routings(code);
                PRINT 'Created routings table';
            END
            ELSE
                PRINT 'routings table already exists';
        """))
        conn.commit()
        print("  routings table ready")

        # =====================================================================
        # Create routing_operations table
        # =====================================================================
        print("Creating routing_operations table...")
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'routing_operations')
            BEGIN
                CREATE TABLE routing_operations (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    routing_id INT NOT NULL,
                    work_center_id INT NOT NULL,

                    -- Sequence
                    sequence INT NOT NULL,
                    operation_code NVARCHAR(50) NULL,
                    operation_name NVARCHAR(200) NULL,
                    description NVARCHAR(MAX) NULL,

                    -- Time (minutes)
                    setup_time_minutes DECIMAL(10,2) DEFAULT 0 NOT NULL,
                    run_time_minutes DECIMAL(10,2) NOT NULL,
                    wait_time_minutes DECIMAL(10,2) DEFAULT 0 NOT NULL,
                    move_time_minutes DECIMAL(10,2) DEFAULT 0 NOT NULL,

                    -- Runtime source: 'manual', 'slicer', 'calculated'
                    runtime_source NVARCHAR(50) DEFAULT 'manual' NOT NULL,
                    slicer_file_path NVARCHAR(500) NULL,

                    -- Quantity
                    units_per_cycle INT DEFAULT 1 NOT NULL,
                    scrap_rate_percent DECIMAL(5,2) DEFAULT 0 NOT NULL,

                    -- Costing overrides
                    labor_rate_override DECIMAL(18,4) NULL,
                    machine_rate_override DECIMAL(18,4) NULL,

                    -- Dependencies
                    predecessor_operation_id INT NULL,
                    can_overlap BIT DEFAULT 0 NOT NULL,

                    -- Status
                    is_active BIT DEFAULT 1 NOT NULL,
                    created_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
                    updated_at DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

                    CONSTRAINT FK_routing_ops_routing FOREIGN KEY (routing_id)
                        REFERENCES routings(id) ON DELETE CASCADE,
                    CONSTRAINT FK_routing_ops_work_center FOREIGN KEY (work_center_id)
                        REFERENCES work_centers(id),
                    CONSTRAINT FK_routing_ops_predecessor FOREIGN KEY (predecessor_operation_id)
                        REFERENCES routing_operations(id)
                );

                CREATE INDEX IX_routing_ops_routing ON routing_operations(routing_id);
                CREATE INDEX IX_routing_ops_work_center ON routing_operations(work_center_id);
                CREATE INDEX IX_routing_ops_sequence ON routing_operations(routing_id, sequence);
                PRINT 'Created routing_operations table';
            END
            ELSE
                PRINT 'routing_operations table already exists';
        """))
        conn.commit()
        print("  routing_operations table ready")

        # =====================================================================
        # Insert default work centers
        # =====================================================================
        print("\nCreating default work centers...")
        conn.execute(text("""
            IF NOT EXISTS (SELECT 1 FROM work_centers WHERE code = 'FDM-POOL')
            BEGIN
                INSERT INTO work_centers (code, name, description, center_type, capacity_hours_per_day, machine_rate_per_hour, is_bottleneck)
                VALUES ('FDM-POOL', 'FDM Printer Pool', 'All FDM 3D printers', 'machine', 200, 2.00, 0);
                PRINT 'Created FDM-POOL work center';
            END

            IF NOT EXISTS (SELECT 1 FROM work_centers WHERE code = 'QC')
            BEGIN
                INSERT INTO work_centers (code, name, description, center_type, capacity_hours_per_day, labor_rate_per_hour)
                VALUES ('QC', 'Quality Control', 'Inspection and testing station', 'station', 8, 25.00);
                PRINT 'Created QC work center';
            END

            IF NOT EXISTS (SELECT 1 FROM work_centers WHERE code = 'ASSEMBLY')
            BEGIN
                INSERT INTO work_centers (code, name, description, center_type, capacity_hours_per_day, labor_rate_per_hour)
                VALUES ('ASSEMBLY', 'Assembly Station', 'Part assembly and hardware insertion', 'station', 8, 20.00);
                PRINT 'Created ASSEMBLY work center';
            END

            IF NOT EXISTS (SELECT 1 FROM work_centers WHERE code = 'SHIPPING')
            BEGIN
                INSERT INTO work_centers (code, name, description, center_type, capacity_hours_per_day, labor_rate_per_hour)
                VALUES ('SHIPPING', 'Packing & Shipping', 'Final packaging and shipping prep', 'station', 8, 18.00);
                PRINT 'Created SHIPPING work center';
            END
        """))
        conn.commit()
        print("  Default work centers created")

        # =====================================================================
        # Summary
        # =====================================================================
        print("\n=== Verifying Tables ===")
        result = conn.execute(text("""
            SELECT name FROM sys.tables
            WHERE name IN ('work_centers', 'resources', 'routings', 'routing_operations')
            ORDER BY name
        """))
        tables = [row[0] for row in result]
        print(f"Tables created: {', '.join(tables)}")

        result = conn.execute(text("SELECT COUNT(*) FROM work_centers"))
        wc_count = result.scalar()
        print(f"Work centers: {wc_count}")

        print("\nMigration completed successfully!")


if __name__ == "__main__":
    run_migration()
