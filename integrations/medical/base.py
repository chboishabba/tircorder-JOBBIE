"""Base classes for national medical record connectors."""

from abc import ABC, abstractmethod
from typing import Dict


class MedicalRecordConnector(ABC):
    """Interface for national medical record systems."""

    @abstractmethod
    def authenticate(self, **credentials) -> None:
        """Authenticate with the remote service."""
        raise NotImplementedError

    @abstractmethod
    def fetch_records(self, patient_id: str) -> Dict:
        """Return patient records in FHIR format."""
        raise NotImplementedError
