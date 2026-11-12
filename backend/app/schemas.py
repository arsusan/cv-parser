from typing import Optional
from pydantic import BaseModel, Field


class Experience(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    start_date: Optional[str] = None   # YYYY-MM
    end_date: Optional[str] = None     # YYYY-MM or 'present'
    description: Optional[str] = None


class CVData(BaseModel):
    name: Optional[str] = None
    linkedin_url: Optional[str] = None
    phone_numbers: list[str] = Field(default_factory=list)
    email_addresses: list[str] = Field(default_factory=list)
    address: Optional[str] = None
    experience: list[Experience] = Field(default_factory=list)
    years_of_experience: Optional[float] = None
    last_working_company: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)


REQUIRED_FIELDS = list(CVData.model_fields.keys())