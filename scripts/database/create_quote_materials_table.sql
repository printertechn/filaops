-- Create quote_materials table for multi-material/multi-color quote support
-- This table stores per-slot material breakdown for AMS multi-color prints

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'quote_materials')
BEGIN
    CREATE TABLE quote_materials (
        id INT IDENTITY(1,1) PRIMARY KEY,
        quote_id INT NOT NULL,
        slot_number INT NOT NULL DEFAULT 1,
        is_primary BIT NOT NULL DEFAULT 0,
        material_type NVARCHAR(50) NOT NULL,
        color_code NVARCHAR(30) NULL,
        color_name NVARCHAR(100) NULL,
        color_hex NVARCHAR(7) NULL,
        material_grams DECIMAL(10,2) NOT NULL,
        created_at DATETIME2 NOT NULL DEFAULT GETDATE(),

        CONSTRAINT FK_quote_materials_quote
            FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE CASCADE
    );

    CREATE INDEX IX_quote_materials_quote_id ON quote_materials(quote_id);

    PRINT 'Created quote_materials table';
END
ELSE
BEGIN
    PRINT 'quote_materials table already exists';
END
GO
