"""Connector for Australia's My Health Record."""

from typing import Dict, Optional

from .base import MedicalRecordConnector


class MyHealthRecordConnector(MedicalRecordConnector):
    """Retrieve records from the Australian My Health Record system."""

    def __init__(self) -> None:
        self.token: Optional[str] = None

    def authenticate(self, token: str) -> None:
        """Store API token for subsequent requests."""
        self.token = token

    def fetch_records(self, patient_id: str) -> Dict:
        """Fetch patient records in FHIR format."""
        raise NotImplementedError(
            "My Health Record API integration not yet implemented"
        )
