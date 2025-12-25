"""
Work Center and Machine models for production scheduling.

Work Centers are logical groups of resources (e.g., "3D Printer Pool", "Assembly Station").
Machines/Resources are physical assets within work centers.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class WorkCenter(Base):
    """
    Work Centers are logical production areas/departments.
    
    Examples:
    - "3D Printer Pool" - Contains multiple 3D printers
    - "Assembly Station" - Manual assembly area
    - "Finishing Department" - Post-processing operations
    """
    __tablename__ = "work_centers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Work Center Type
    center_type = Column(String(50), default="production", nullable=False)  # production, assembly, finishing, etc.
    
    # Capacity Planning
    capacity_hours_per_day = Column(Numeric(10, 2), nullable=True)
    capacity_units_per_hour = Column(Numeric(10, 2), nullable=True)
    
    # Costing - multiple rate types for detailed job costing
    machine_rate_per_hour = Column(Numeric(18, 4), nullable=True)
    labor_rate_per_hour = Column(Numeric(18, 4), nullable=True)
    overhead_rate_per_hour = Column(Numeric(18, 4), nullable=True)
    
    # Simplified hourly rate (for backward compatibility and simple costing)
    hourly_rate = Column(Numeric(10, 2), default=0, nullable=False)
    
    # Scheduling
    is_bottleneck = Column(Boolean, default=False, nullable=False)
    scheduling_priority = Column(Integer, default=5, nullable=False)  # 1=highest, 10=lowest
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    machines = relationship("Machine", back_populates="work_center", cascade="all, delete-orphan")
    operations = relationship("ProductionOrderOperation", back_populates="work_center")
    printers = relationship("Printer", back_populates="work_center")
    resources = relationship("Resource", back_populates="work_center", cascade="all, delete-orphan")
    routing_operations = relationship("RoutingOperation", back_populates="work_center")
    
    def __repr__(self):
        return f"<WorkCenter {self.code}: {self.name}>"

    @property
    def total_rate_per_hour(self):
        """Combined hourly rate (machine + labor + overhead)"""
        machine = float(self.machine_rate_per_hour or 0)
        labor = float(self.labor_rate_per_hour or 0)
        overhead = float(self.overhead_rate_per_hour or 0)
        return machine + labor + overhead

    @property
    def available_machine_count(self):
        """Number of available machines in this work center"""
        return len([m for m in self.machines if m.is_available])

    @property
    def total_machine_count(self):
        """Total number of machines in this work center"""
        return len(self.machines)


class Machine(Base):
    """
    Physical machines/resources within work centers.
    
    Examples:
    - "PRINTER-001" - Bambu X1 Carbon #1
    - "PRINTER-002" - Bambu X1 Carbon #2  
    - "ASM-001" - Assembly Station #1
    """
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    work_center_id = Column(Integer, ForeignKey('work_centers.id'), nullable=False)
    
    # Machine type and capabilities
    machine_type = Column(String(100), nullable=True)  # "3d_printer", "assembly_station", "cnc_mill", etc.
    compatible_materials = Column(String(500), nullable=True)  # "PLA,PETG,ABS" for printers
    
    # Status: available, busy, maintenance, offline
    status = Column(String(50), default="available", nullable=False, index=True)
    
    # Physical properties
    bed_size_x = Column(Numeric(10, 2), nullable=True)  # For 3D printers: bed size in mm
    bed_size_y = Column(Numeric(10, 2), nullable=True)
    bed_size_z = Column(Numeric(10, 2), nullable=True)
    
    # Scheduling
    active = Column(Boolean, default=True, nullable=False)
    
    # Integration
    bambu_serial = Column(String(100), nullable=True)  # For Bambu printer integration
    bambu_access_code = Column(String(20), nullable=True)
    bambu_ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    
    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    work_center = relationship("WorkCenter", back_populates="machines")
    operations = relationship("ProductionOrderOperation", back_populates="resource")
    
    def __repr__(self):
        return f"<Machine {self.code}: {self.name} ({self.status})>"

    @property
    def is_available(self):
        """True if machine is available for scheduling"""
        return self.active and self.status == "available"

    @property
    def is_3d_printer(self):
        """True if this machine is a 3D printer"""
        return self.machine_type == "3d_printer" or "printer" in self.name.lower()

    @property
    def bed_volume_mm3(self):
        """Bed volume in cubic millimeters (for 3D printers)"""
        if self.bed_size_x and self.bed_size_y and self.bed_size_z:
            return float(self.bed_size_x) * float(self.bed_size_y) * float(self.bed_size_z)
        return None

    def supports_material(self, material_code: str) -> bool:
        """Check if machine supports a specific material"""
        if not self.compatible_materials:
            return True  # If not specified, assume all materials supported
        
        materials = [m.strip().upper() for m in self.compatible_materials.split(',')]
        return material_code.upper() in materials


# Alias for backward compatibility
Resource = Machine
