"""Connectors for national medical record systems."""

from .base import MedicalRecordConnector
from .doctor_notes_folder import DoctorNotesFolderConnector
from .fhir_export import FHIRExportConnector
from .my_health_record import MyHealthRecordConnector
from .scan_folder import ScanFolderConnector

CONNECTORS = {
    "AU": MyHealthRecordConnector,
}

EXPORT_CONNECTORS = {
    "FHIR_EXPORT": FHIRExportConnector,
    "DOCTOR_NOTES_FOLDER": DoctorNotesFolderConnector,
    "SCAN_FOLDER": ScanFolderConnector,
}

__all__ = [
    "MedicalRecordConnector",
    "MyHealthRecordConnector",
    "FHIRExportConnector",
    "DoctorNotesFolderConnector",
    "ScanFolderConnector",
    "CONNECTORS",
    "EXPORT_CONNECTORS",
]
