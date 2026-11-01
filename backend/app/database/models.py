from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base

class Product(Base):
    """Product master entity table."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    product_code = Column(String, unique=True, index=True, nullable=False)
    product_name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    price = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sales = relationship("Sale", back_populates="product", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="product", uselist=False, cascade="all, delete-orphan")
    forecasts = relationship("Forecast", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(code='{self.product_code}', name='{self.product_name}')>"


class Sale(Base):
    """Historical sales transaction entity table."""
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    sale_date = Column(Date, nullable=False, index=True)
    quantity_sold = Column(Float, nullable=False)
    promotion = Column(Integer, default=0)  # 0 = No promotion, 1 = Promoted
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    product = relationship("Product", back_populates="sales")

    def __repr__(self):
        return f"<Sale(product_id={self.product_id}, date={self.sale_date}, qty={self.quantity_sold})>"


class Inventory(Base):
    """User-simulated inventory status entity table."""
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), unique=True, nullable=False, index=True)
    current_stock = Column(Float, default=0.0, nullable=False)
    safety_stock = Column(Float, default=0.0, nullable=False)
    supplier_lead_time = Column(Integer, default=1, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    product = relationship("Product", back_populates="inventory")

    def __repr__(self):
        return f"<Inventory(product_id={self.product_id}, stock={self.current_stock})>"


class Forecast(Base):
    """Generated 7-day demand forecast predictions table."""
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    forecast_date = Column(Date, nullable=False)
    predicted_demand = Column(Float, nullable=False)
    model_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    product = relationship("Product", back_populates="forecasts")

    def __repr__(self):
        return f"<Forecast(product_id={self.product_id}, date={self.forecast_date}, pred={self.predicted_demand})>"


class ModelResult(Base):
    """Machine learning evaluation benchmark metrics table."""
    __tablename__ = "model_results"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False)
    mae = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    mape = Column(Float, nullable=False)
    training_date = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ModelResult(model='{self.model_name}', MAE={self.mae}, RMSE={self.rmse}, MAPE={self.mape})>"


class DatasetMetadata(Base):
    """Stores metadata about uploaded and cleaned retail sales datasets."""
    __tablename__ = "dataset_metadata"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_size_bytes = Column(Integer, default=0)
    original_rows = Column(Integer, default=0)
    original_columns = Column(Integer, default=0)
    cleaned_rows = Column(Integer, default=0)
    cleaned_columns = Column(Integer, default=0)
    status = Column(String, default="uploaded")  # 'uploaded', 'cleaned', 'ready'
    column_mappings = Column(String, nullable=True)  # JSON string of role mappings
    quality_summary = Column(String, nullable=True)  # JSON string of quality findings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<DatasetMetadata(filename='{self.filename}', rows={self.original_rows}, status='{self.status}')>"
