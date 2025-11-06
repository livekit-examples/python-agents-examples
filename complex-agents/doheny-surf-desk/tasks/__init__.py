"""Task implementations for Doheny Surf Desk."""

from tasks.name_task import NameTask, NameResult
from tasks.phone_task import PhoneTask, PhoneResult
from tasks.age_task import AgeTask, AgeResult
from tasks.email_task import GetEmailTask
from tasks.experience_task import ExperienceTask, ExperienceResult
from tasks.preferences_task import PreferencesTask, PreferencesResult
from tasks.consent_task import ConsentTask
from tasks.notification_task import NotificationTask, NotificationResult
from tasks.payment_details_task import PaymentDetailsTask, PaymentDetailsResult

__all__ = [
    'NameTask',
    'NameResult',
    'PhoneTask',
    'PhoneResult',
    'AgeTask',
    'AgeResult',
    'GetEmailTask',
    'ExperienceTask',
    'ExperienceResult',
    'PreferencesTask',
    'PreferencesResult',
    'ConsentTask',
    'NotificationTask',
    'NotificationResult',
    'PaymentDetailsTask',
    'PaymentDetailsResult',
]
