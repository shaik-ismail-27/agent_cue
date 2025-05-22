from typing import Any, Dict, List, Text
import logging
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk.executor import CollectingDispatcher

# Set up logging
logger = logging.getLogger(__name__)

class ActionCheckRequiredSlotsAvailable(Action):
    def name(self) -> Text:
        return "action_check_required_slots_available"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        current_flow = tracker.get_slot("current_flow")
        logger.info(f"Checking required slots for flow: {current_flow}")
        
        flow_required_slots = {
            "clinic_selection": ["selected_service_type", "city", "state", "clinic_recommendation_status"],
            "suggest_alternative_slots": ["selected_service_type", "city", "state", "clinic_recommendation_status", "selected_clinic"],
            "gather_booking_data": ["selected_service_type", "city", "state", "clinic_recommendation_status", "selected_clinic", "appointment_date", "appointment_time"],
            "check_availability": ["selected_clinic", "appointment_date", "appointment_time"],
            "book_appointment": ["selected_service_type", "city", "state", "clinic_recommendation_status", "selected_clinic", "appointment_date", "appointment_time", "patient_name", "patient_age"],
            "booking_after_payment": ["selected_service_type", "city", "state", "clinic_recommendation_status", "selected_clinic", "appointment_date", "appointment_time", "patient_name", "patient_age", "payment_status"],
            "booking_without_payment": ["selected_service_type", "city", "state", "clinic_recommendation_status", "selected_clinic", "appointment_date", "appointment_time", "patient_name", "patient_age"],
            "make_payment": ["selected_service_type", "city", "state", "clinic_recommendation_status", "selected_clinic", "appointment_date", "appointment_time", "patient_name", "patient_age", "booking_payment_requirement", "conform_booking_with_payment"],
            "payment_retry_new_card": ["selected_service_type", "city", "state", "clinic_recommendation_status", "selected_clinic", "appointment_date", "appointment_time", "patient_name", "patient_age", "booking_payment_requirement", "conform_booking_with_payment", "payment_retry_type"],
            "payment_retry_same_card": ["selected_service_type", "city", "state", "clinic_recommendation_status", "selected_clinic", "appointment_date","appointment_time", "patient_name", "patient_age", "booking_payment_requirement", "conform_booking_with_payment", "payment_retry_type"],
            "start_account_creation": ["selected_service_type", "city", "state", "clinic_recommendation_status", "selected_clinic", "patient_name", "patient_age"],
            "start_account_authentication": ["selected_service_type", "city", "state", "clinic_recommendation_status", "selected_clinic", "appointment_date", "appointment_time", "patient_name", "patient_age"],
            "auth_otp_handler": ["selected_service_type", "city", "state", "clinic_recommendation_status", "selected_clinic", "appointment_date", "appointment_time", "patient_name", "patient_age", "registered_phone_number", "auth_initiated"]
        }
        
        if current_flow == "authenticate_account":
            has_account = tracker.get_slot("has_account")
            if has_account is not True and has_account != "true":
                logger.info("authenticate_account flow requires has_account to be true")
                dispatcher.utter_message(text="This flow is only for users with existing accounts.")
                return [SlotSet("slots_available", "error"), 
                        SlotSet("missing_slots", ["has_account"])]
        
        if current_flow == "create_account":
            has_account = tracker.get_slot("has_account")
            if has_account is not False and has_account != "false":
                logger.info("create_account flow requires has_account to be false")
                dispatcher.utter_message(text="This flow is only for users who don't have an account yet.")
                return [SlotSet("slots_available", "error"), 
                        SlotSet("missing_slots", ["has_account"])]
        
        if current_flow == "book_appointment":
            authentication_status = tracker.get_slot("authentication_status")
            account_creation = tracker.get_slot("account_creation")
            
            if (authentication_status != "success" and account_creation != "success"):
                logger.info("book_appointment flow requires either authentication_status==success or account_creation==success")
                dispatcher.utter_message(text="You need to either log in or create an account before booking an appointment.")
                return [SlotSet("slots_available", "error"), 
                        SlotSet("missing_slots", ["authentication_status", "account_creation"])]
        
        if current_flow == "make_payment":
            authentication_status = tracker.get_slot("authentication_status")
            account_creation = tracker.get_slot("account_creation")
            booking_payment_requirement = tracker.get_slot("booking_payment_requirement")
            conform_booking_with_payment = tracker.get_slot("conform_booking_with_payment")
            
            missing_payment_slots = []
            
            if (authentication_status != "success" and account_creation != "success"):
                logger.info("make_payment flow requires either authentication_status==success or account_creation==success")
                missing_payment_slots.extend(["authentication_status", "account_creation"])
            
            if booking_payment_requirement is not True and booking_payment_requirement != "true":
                logger.info("make_payment flow requires booking_payment_requirement to be true")
                missing_payment_slots.append("booking_payment_requirement")
            
            if conform_booking_with_payment is not True and conform_booking_with_payment != "true":
                logger.info("make_payment flow requires conform_booking_with_payment to be true")
                missing_payment_slots.append("conform_booking_with_payment")
            
            if missing_payment_slots:
                dispatcher.utter_message(text="There was an issue with your payment setup. Please go through the booking process again.")
                return [SlotSet("slots_available", "error"), 
                        SlotSet("missing_slots", missing_payment_slots)]
        
        if current_flow in ["payment_retry_new_card", "payment_retry_same_card"]:
            authentication_status = tracker.get_slot("authentication_status")
            account_creation = tracker.get_slot("account_creation")
            booking_payment_requirement = tracker.get_slot("booking_payment_requirement")
            conform_booking_with_payment = tracker.get_slot("conform_booking_with_payment")
            payment_retry_type = tracker.get_slot("payment_retry_type")
            
            missing_payment_slots = []
            
            if (authentication_status != "success" and account_creation != "success"):
                logger.info("payment retry flow requires either authentication_status==success or account_creation==success")
                missing_payment_slots.extend(["authentication_status", "account_creation"])
            
            if booking_payment_requirement is not True and booking_payment_requirement != "true":
                logger.info("payment retry flow requires booking_payment_requirement to be true")
                missing_payment_slots.append("booking_payment_requirement")
            
            if conform_booking_with_payment is not True and conform_booking_with_payment != "true":
                logger.info("payment retry flow requires conform_booking_with_payment to be true")
                missing_payment_slots.append("conform_booking_with_payment")
            
            if current_flow == "payment_retry_new_card" and payment_retry_type != "new_card":
                logger.info("payment_retry_new_card flow requires payment_retry_type to be new_card")
                missing_payment_slots.append("payment_retry_type")
            elif current_flow == "payment_retry_same_card" and payment_retry_type != "same_card":
                logger.info("payment_retry_same_card flow requires payment_retry_type to be same_card")
                missing_payment_slots.append("payment_retry_type")
            
            if missing_payment_slots:
                dispatcher.utter_message(text="There was an issue with your payment retry setup. Please try again.")
                return [SlotSet("slots_available", "error"), 
                        SlotSet("missing_slots", missing_payment_slots)]
        
        if current_flow == "otp_handler":
            auth_initiated = tracker.get_slot("auth_initiated")
            registered_phone_number = tracker.get_slot("registered_phone_number")
            
            missing_slots = []
            
            if not registered_phone_number:
                logger.info("otp_handler flow requires registered_phone_number")
                missing_slots.append("registered_phone_number")
                
            if auth_initiated is not True and auth_initiated != "true":
                logger.info("otp_handler flow requires auth_initiated to be true")
                missing_slots.append("auth_initiated")
            
            if missing_slots:
                dispatcher.utter_message(text="Please complete account authentication initiation first.")
                return [SlotSet("slots_available", "error"), 
                        SlotSet("missing_slots", missing_slots)]
        
        if current_flow == "start_account_authentication":
            selected_service_type = tracker.get_slot("selected_service_type")
            selected_clinic = tracker.get_slot("selected_clinic")
            
            missing_slots = []
            
            if not selected_service_type:
                logger.info("start_account_authentication flow requires selected_service_type")
                missing_slots.append("selected_service_type")
                
            if not selected_clinic:
                logger.info("start_account_authentication flow requires selected_clinic")
                missing_slots.append("selected_clinic")
            
            if missing_slots:
                dispatcher.utter_message(text="Please select a service and clinic before authenticating your account.")
                return [SlotSet("slots_available", "error"), 
                        SlotSet("missing_slots", missing_slots)]
        
        if not current_flow or current_flow not in flow_required_slots:
            logger.warning(f"Unknown flow: {current_flow}, defaulting to all slots available")
            return [SlotSet("slots_available", "success"),
                   SlotSet("missing_slots", None)]
        
        required_slots = flow_required_slots[current_flow]
        
        missing_slots = []
        for slot_name in required_slots:
            slot_value = tracker.get_slot(slot_name)
            if slot_value is None:
                missing_slots.append(slot_name)
        
        if missing_slots:
            logger.info(f"Missing required slots for flow {current_flow}: {missing_slots}")
            
            slot_display_names = {
                "city": "city",
                "state": "state",
                "selected_clinic": "clinic",
                "appointment_date": "appointment date",
                "appointment_time": "appointment time",
                "patient_name": "patient name",
                "patient_age": "patient age",
                "card_number": "card number",
                "card_expiry_month": "card expiry month",
                "card_expiry_year": "card expiry year",
                "card_cvv": "card security code",
                "user_name": "your name",
                "user_phone_number": "your phone number",
                "registered_phone_number": "registered phone number",
                "account_auth_otp_action": "verification code",
                "selected_service_type": "service type",
                "clinic_recommendation_status": "clinic recommendations",
                "date_time_finalized": "appointment date and time",
                "has_account": "account status",
                "payment_status": "payment status",
                "authentication_status": "authentication status",
                "account_creation": "account creation status",
                "booking_payment_requirement": "payment requirement",
                "conform_booking_with_payment": "payment confirmation",
                "payment_retry_type": "payment retry method"
            }
            
            formatted_missing_slots = [slot_display_names.get(slot, slot) for slot in missing_slots]
            
            if len(formatted_missing_slots) == 1:
                message = f"I need to know your {formatted_missing_slots[0]} to proceed."
            else:
                slots_text = ", ".join(formatted_missing_slots[:-1]) + f" and {formatted_missing_slots[-1]}"
                message = f"I need to know your {slots_text} to proceed."
            
            dispatcher.utter_message(text=message)
            return [SlotSet("slots_available", "error"), 
                    SlotSet("missing_slots", missing_slots)]
        
        logger.info(f"All required slots for flow {current_flow} are available")
        return [SlotSet("slots_available", "success"),
                SlotSet("missing_slots", None)]

class ActionResetSlots(Action):
    def name(self) -> Text:
        return "action_reset_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        logger.info("Resetting all slots")
        return [AllSlotsReset()]

class ActionEndBookingProcess(Action):
    def name(self) -> Text:
        return "action_end_booking_process"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        return [] 