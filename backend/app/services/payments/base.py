from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class InitiatedPayment:
    reference: str
    authorization_url: str | None  # None for providers that don't use a hosted checkout


@dataclass
class VerifiedPayment:
    success: bool
    reference: str
    amount_ngn: int
    raw: dict


class PaymentProvider(ABC):
    """Common interface for anything that can take money from a renter/landlord."""

    @abstractmethod
    def initiate(self, amount_ngn: int, email: str, metadata: dict, callback_url: str | None = None) -> InitiatedPayment:
        raise NotImplementedError

    @abstractmethod
    def verify(self, reference: str) -> VerifiedPayment:
        raise NotImplementedError
