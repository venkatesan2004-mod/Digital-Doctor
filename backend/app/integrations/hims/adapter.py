import abc
import uuid
from typing import Dict, Any
from app.core.logging import logger
from app.core.config import settings


class HIMSAdapterBase(abc.ABC):
    """Abstract interface for Hospital Information Management System (HIMS) integration."""

    @abc.abstractmethod
    def dispatch_direct_consultation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches a direct doctor registration to the hospital HIMS."""
        pass

    @abc.abstractmethod
    def fetch_patient_demographics(self, mrn: str) -> Dict[str, Any]:
        """Fetches authoritative master patient demographics from HIMS."""
        pass


class MockHIMSAdapter(HIMSAdapterBase):
    """Synthetic in-memory HIMS integration adapter for local development and testing."""

    def dispatch_direct_consultation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        hims_ticket = f"HIMS-TKT-{uuid.uuid4().hex[:8].upper()}"
        logger.info(
            f"[MOCK HIMS] Direct doctor consultation dispatched to external HIMS queue. "
            f"Ticket={hims_ticket} Patient={payload.get('first_name')} {payload.get('last_name')}"
        )
        return {
            "status": "DISPATCHED_TO_HIMS",
            "hims_ticket_number": hims_ticket,
            "message": "Patient registered successfully in standard OPD queue. Proceed to Doctor Consultation Room.",
            "workflow": "DIRECT_DOCTOR_HIMS",
            "queue_position": 4,
            "estimated_wait_minutes": 25,
        }

    def fetch_patient_demographics(self, mrn: str) -> Dict[str, Any]:
        return {
            "mrn": mrn,
            "source": "SYNTHETIC_HIMS_GATEWAY",
            "status": "ACTIVE"
        }


def get_hims_adapter() -> HIMSAdapterBase:
    """Factory returning configured HIMS adapter."""
    return MockHIMSAdapter()
