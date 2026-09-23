"""Pluggable alert delivery interface.

Per PLAN.md Section 2.2, real SMS/push notification delivery requires
institutional partnership, so all channels here are mocked/log-only.
The interface is designed so a real provider can be plugged in later
by implementing the ``AlertChannel`` base class.
"""

import abc
import logging

logger = logging.getLogger(__name__)


class AlertChannel(abc.ABC):
    """Abstract base class for alert delivery channels."""

    @abc.abstractmethod
    def send(self, alert: dict) -> bool:
        """Send an alert through this channel.

        Args:
            alert: dict with keys like severity, district_name, message, etc.

        Returns:
            True if delivery succeeded (or was simulated successfully).
        """
        ...

    @abc.abstractmethod
    def channel_name(self) -> str:
        """Human-readable channel name."""
        ...


class MockLogChannel(AlertChannel):
    """Log-only channel -- writes alerts to Python logger.

    This is the default channel used in the current build.
    Replace with a real SMS/email provider by subclassing AlertChannel.
    """

    def channel_name(self) -> str:
        return "mock_log"

    def send(self, alert: dict) -> bool:
        severity = alert.get("severity", "INFO")
        district = alert.get("district_name", "?")
        date = alert.get("date", "?")
        logger.info(
            "[%s] %s | %s on %s: %s",
            self.channel_name(),
            severity,
            district,
            date,
            alert.get("message", ""),
        )
        return True


class MockSMSChannel(AlertChannel):
    """Simulated SMS delivery -- logs what would be sent.

    Extension point: replace the body of ``send()`` with actual
    Twilio / AWS SNS / telecom gateway calls.
    """

    def channel_name(self) -> str:
        return "mock_sms"

    def send(self, alert: dict) -> bool:
        logger.info(
            "[%s] Would send SMS for %s: %s",
            self.channel_name(),
            alert.get("district_name", "?"),
            alert.get("message", "")[:160],  # SMS length limit
        )
        return True


class MockEmailChannel(AlertChannel):
    """Simulated email delivery -- logs what would be sent.

    Extension point: replace with SMTP / SendGrid / SES calls.
    """

    def channel_name(self) -> str:
        return "mock_email"

    def send(self, alert: dict) -> bool:
        logger.info(
            "[%s] Would email for %s: severity=%s, message=%s",
            self.channel_name(),
            alert.get("district_name", "?"),
            alert.get("severity", "?"),
            alert.get("message", ""),
        )
        return True
