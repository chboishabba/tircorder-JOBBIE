"""Connectors for national medical record systems."""

from .base import MedicalRecordConnector
from .my_health_record import MyHealthRecordConnector

CONNECTORS = {
    "AU": MyHealthRecordConnector,
}

__all__ = ["MedicalRecordConnector", "MyHealthRecordConnector", "CONNECTORS"]
