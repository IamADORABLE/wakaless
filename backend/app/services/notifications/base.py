from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class NotificationResult:
    success: bool
    provider_reference: str | None
    raw: dict


class EmailProvider(ABC):
    @abstractmethod
    def send(self, to_email: str, subject: str, body: str) -> NotificationResult:
        raise NotImplementedError


class SmsProvider(ABC):
    @abstractmethod
    def send(self, to_phone: str, message: str) -> NotificationResult:
        raise NotImplementedError
