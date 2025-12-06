"""
Printer model
"""
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.db.base import Base

class Printer(Base):
    """Printer model - matches printers table"""
    __tablename__ = "printers"

    id = Column(Integer, primary_key=True, index=True)

    # Printer identification
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    model = Column(String(100), nullable=False)
    serial_number = Column(String(100), nullable=True)

    # Network
    ip_address = Column(String(50), nullable=True)
    mqtt_topic = Column(String(255), nullable=True)

    # Status
    status = Column(String(50), nullable=True, default='offline')
    # offline, idle, printing, paused, error, maintenance

    # Location
    location = Column(String(255), nullable=True)

    # Active flag
    active = Column(Boolean, default=True, nullable=True)

    # Relationships
    print_jobs = relationship("PrintJob", back_populates="printer")

    def __repr__(self):
        return f"<Printer {self.code}: {self.name} ({self.status})>"
