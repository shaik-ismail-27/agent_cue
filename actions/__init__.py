from typing import Dict, Text, Any, List
import logging

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

from actions.general_health_actions import (
    ActionRecommendGeneralCheckupClinics,
    ActionBookGeneralCheckupAppointment
)

from actions.specialized_service_actions import (
    ActionRecommendSpecialistClinics,
    ActionBookSpecialistAppointment
)


from actions.location_clinic_actions import (
    ActionSetCityState,
    ActionValidateClinicSelection,
    ActionValidateAppointmentDate
)

from actions.appointment_slot_actions import (
    ActionSuggestAlternativeTimeSlots,
    ActionProcessSelectedSlot,
    ActionCheckAppointmentSlot
)

from actions.payment_actions import (
    ActionCheckAccountPaymentMethodNeeded,
    ActionCheckBookingPaymentRequirement,
    ActionSendPaymentRequest,
    ActionVerifyPaymentOTP,
    ActionCheckPaymentStatus
)

from actions.account_actions import (
    ActionCreateAccount,
    ActionAddPaymentMethod,
    ActionVerifyAccount,
    ActionCheckAuthStatus,
    ActionResendAuthOTP
)

from actions.system_actions import (
    ActionCheckRequiredSlotsAvailable,
    ActionResetSlots,
    ActionEndBookingProcess
)

# Define the list of actions for Rasa to register
__all__ = [
    "ActionRecommendGeneralCheckupClinics",
    "ActionCheckAppointmentSlot",
    "ActionBookGeneralCheckupAppointment",
    "ActionRecommendSpecialistClinics",
    "ActionBookSpecialistAppointment",
    "ActionSuggestAlternativeTimeSlots",
    "ActionProcessSelectedSlot",
    "ActionCheckAppointmentSlot",
    "ActionSendPaymentRequest",
    "ActionAddPaymentMethod",
    "ActionCheckBookingPaymentRequirement",
    "ActionCheckAccountPaymentMethodNeeded",
    "ActionCheckPaymentStatus",
    "ActionCreateAccount",
    "ActionSetCityState",
    "ActionValidateClinicSelection",
    "ActionResendAuthOTP",
    "ActionCheckAuthStatus",
    "ActionEndBookingProcess",
    "ActionValidateAppointmentDate",
    "ActionVerifyPaymentOTP",
    "ActionVerifyAccount",
    "ActionCheckRequiredSlotsAvailable",
    "ActionResetSlots"
]
