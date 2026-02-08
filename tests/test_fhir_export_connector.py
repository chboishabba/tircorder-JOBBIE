from datetime import datetime, timezone
import json

from integrations.medical import FHIRExportConnector


def test_fhir_export_meta_only_and_attachment_data_not_emitted(tmp_path):
    collected_at = datetime(2026, 2, 8, 12, 0, 0, tzinfo=timezone.utc)
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "p1",
                    "meta": {"lastUpdated": "2026-02-01T10:00:00Z"},
                    "name": [{"family": "Doe", "given": ["Jane"]}],
                    "address": [{"text": "123 Fake St"}],
                }
            },
            {
                "resource": {
                    "resourceType": "DocumentReference",
                    "id": "d1",
                    "date": "2026-02-02T03:04:05Z",
                    "content": [
                        {
                            "attachment": {
                                "contentType": "application/pdf",
                                "title": "Visit Summary",
                                "data": "VEhJUyBJUyBCQVNFMjY0",  # base64-ish
                            }
                        }
                    ],
                }
            },
        ],
    }
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")

    connector = FHIRExportConnector(hash_salt="salt")
    events = connector.load(path, collected_at=collected_at)

    assert len(events) == 2

    patient = next(e for e in events if e["details"]["resource_type"] == "Patient")
    assert patient["timestamp"] == "2026-02-01T10:00:00+00:00"
    assert "name" not in patient["details"]
    assert "address" not in patient["details"]

    doc = next(e for e in events if e["details"]["resource_type"] == "DocumentReference")
    assert doc["timestamp"] == "2026-02-02T03:04:05+00:00"
    refs = doc["details"].get("attachment_refs") or []
    assert refs and refs[0]["has_data"] is True
    # Ensure the base64-ish payload is not emitted into the story event stream.
    assert "VEhJUyBJUyBCQVNFMjY0" not in json.dumps(doc["details"])
