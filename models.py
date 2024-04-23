from controller import Base
from sqlalchemy import TIMESTAMP,Integer ,Column, String, Boolean,UniqueConstraint
from sqlalchemy.sql import func
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
from datetime import datetime
from typing import List,Optional
from pydantic import BaseModel


class System(Base):
    __tablename__ = "systems"
    unique_id = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE)
    id = Column(Integer, nullable=False)
    domain_name = Column(String, nullable=False)
    table_name = Column(String, nullable=False)
    field_name = Column(String, nullable=False)
    alias_name = Column(String, nullable=False)
    createdon = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    updatedon = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('table_name', 'field_name', name='uq_table_field'),
        #UniqueConstraint('table_name','alias_name', name='uq_alias_name'),
    )

class SystemBaseSchema(BaseModel):
    unique_id: str | None = None
    id: int 
    domain_name: str
    table_name: str
    field_name:str
    alias_name:str    
    createdon: Optional[datetime] = None
    updatedon: Optional[datetime] = None
   
    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        arbitrary_types_allowed = True

class ListsystemResponse(BaseModel):
    status: str
    results: int
    systems: List[SystemBaseSchema]
