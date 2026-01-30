"""
Data models for Product Discovery Service
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class MarketplaceEnum(str, Enum):
    """Supported Amazon marketplaces"""
    US = "US"
    UK = "UK"
    DE = "DE"
    FR = "FR"
    IT = "IT"
    ES = "ES"
    CA = "CA"
    JP = "JP"


class UserTier(str, Enum):
    """User subscription tier"""
    FREE = "free"
    PRO = "pro"


class DiscoveryRequest(BaseModel):
    """Request model for product discovery analysis"""
    # Core fields
    category: str = Field(..., description="Product category (e.g., 'Kitchen & Dining')")
    keywords: str = Field(..., description="Product keywords (e.g., 'coffee maker')")
    marketplace: MarketplaceEnum = Field(default=MarketplaceEnum.US, description="Amazon marketplace")
    
    # Optional fields
    reference_asins: Optional[List[str]] = Field(default=None, description="Reference ASINs for analysis")
    
    # User info
    user_name: Optional[str] = Field(default="Valued Customer", description="User's name")
    user_email: str = Field(..., description="User's email for report delivery")
    user_industry: Optional[str] = Field(default=None, description="User's industry/business type")
    
    # Subscription tier
    user_tier: UserTier = Field(default=UserTier.FREE, description="User subscription level")
    selected_model: Optional[str] = Field(default=None, description="Pro users can select model")
    
    # Advanced Pro Config
    analysis_focus: Optional[List[str]] = Field(default=None, description="Specific focus areas")
    analysis_prompt: Optional[str] = Field(default=None, description="Custom analysis prompt")
    report_language: Optional[str] = Field(default="English", description="Target language for report")


class WebSource(BaseModel):
    """Web content source"""
    url: str
    title: str
    content: str
    source_type: str  # "reddit", "youtube", "blog", etc.


class AmazonProduct(BaseModel):
    """Amazon product data"""
    asin: str
    title: str
    price: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    features: Optional[List[str]] = None
    reviews: Optional[List[dict]] = None


class AnalysisReport(BaseModel):
    """Generated analysis report"""
    model_config = {"protected_namespaces": ()}  # Allow model_ prefix
    
    report_id: str
    user_email: str
    category: str
    keywords: str
    marketplace: str
    
    # Report content
    report_markdown: str
    report_html: str
    
    # Metadata
    generated_at: str
    model_used: str
    sources_count: int
    asins_analyzed: int


class DiscoveryResponse(BaseModel):
    """Response for discovery request"""
    success: bool
    message: str
    report_id: Optional[str] = None
    report_preview: Optional[str] = None  # First 500 chars
    estimated_delivery_minutes: int = 5
