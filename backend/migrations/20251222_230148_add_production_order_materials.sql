-- Migration: Add production_order_materials table for material substitutions
-- Date: 2025-12-22
-- Purpose: Track material substitutions and quantity adjustments during production

-- Create production_order_materials table
CREATE TABLE IF NOT EXISTS production_order_materials (
    id SERIAL PRIMARY KEY,
    production_order_id INTEGER NOT NULL REFERENCES production_orders(id) ON DELETE CASCADE,
    bom_line_id INTEGER REFERENCES bom_lines(id) ON DELETE SET NULL,
    
    -- Original material from BOM
    original_product_id INTEGER NOT NULL REFERENCES products(id),
    original_quantity NUMERIC(18, 4) NOT NULL,
    
    -- Substituted/adjusted material
    substitute_product_id INTEGER NOT NULL REFERENCES products(id),
    planned_quantity NUMERIC(18, 4) NOT NULL,
    actual_quantity_used NUMERIC(18, 4),
    
    -- Audit trail
    reason TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    
    -- Indexes
    CONSTRAINT production_order_materials_pkey PRIMARY KEY (id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_po_materials_production_order 
    ON production_order_materials(production_order_id);

CREATE INDEX IF NOT EXISTS idx_po_materials_original_product 
    ON production_order_materials(original_product_id);

CREATE INDEX IF NOT EXISTS idx_po_materials_substitute_product 
    ON production_order_materials(substitute_product_id);

-- Add comments for documentation
COMMENT ON TABLE production_order_materials IS 'Material substitutions and quantity adjustments for production orders';
COMMENT ON COLUMN production_order_materials.original_product_id IS 'Material specified in BOM';
COMMENT ON COLUMN production_order_materials.substitute_product_id IS 'Material actually used (can be same as original if only qty adjusted)';
COMMENT ON COLUMN production_order_materials.original_quantity IS 'Quantity from BOM calculation';
COMMENT ON COLUMN production_order_materials.planned_quantity IS 'Adjusted quantity to use';
COMMENT ON COLUMN production_order_materials.actual_quantity_used IS 'Actual quantity consumed (recorded on completion)';
COMMENT ON COLUMN production_order_materials.reason IS 'Why material was substituted or quantity adjusted';

