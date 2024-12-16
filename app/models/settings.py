from sqlalchemy import Column, Boolean, Integer

from app.database_setup import DefaultBase


class SettingsModel(DefaultBase):
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True)
    api_authentication = Column(Boolean, default=True)
    gcloud = Column(Boolean, default=True)