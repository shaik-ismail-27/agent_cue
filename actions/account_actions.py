from typing import Any, Dict, List, Text
import logging
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from actions.backend_client import backend

# Set up logging
logger = logging.getLogger(__name__)

class ActionCreateAccount(Action):
    def name(self) -> Text:
        return "action_create_account"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        user_phone_number = tracker.get_slot("user_phone_number")
        user_name = tracker.get_slot("user_name")
        otp = tracker.get_slot("otp")
        
        selected_clinic = tracker.get_slot("selected_clinic")
        appointment_date = tracker.get_slot("appointment_date")
        appointment_time = tracker.get_slot("appointment_time")
        patient_name = tracker.get_slot("patient_name")
        patient_age = tracker.get_slot("patient_age")
        payment_required = tracker.get_slot("payment_required")
        
        if otp:
            if not user_phone_number:
                dispatcher.utter_message(text="Missing required information. Please provide your phone number.")
                return [SlotSet("account_creation", "error")]
                
            try:
                logger.info(f"Verifying account creation OTP for phone number {user_phone_number}")
                response = backend.verify_account(
                    phone_number=user_phone_number,
                    otp=otp
                )
                
                if response.get("status") == "success":
                    return [SlotSet("account_creation", "success"), SlotSet("reached_clinic", "success")]
                else:
                    error_message = response.get("message", "Invalid verification code")
                    error_type = response.get("error_type", "")
                    logger.error(f"Account verification failed: {error_message}")
                    
                    if error_type == "user_exists":
                        dispatcher.utter_message(text="An account already exists with this phone number. Please try again with a different number or logging in.")
                        return [
                            SlotSet("account_creation", "error"),
                            SlotSet("user_exists", True),
                            SlotSet("reached_clinic", "success")
                        ]
                    elif error_type == "invalid_otp":
                        return [
                            SlotSet("account_creation", "error"),
                            SlotSet("reached_clinic", "success")
                        ]
                    elif error_type == "network_error":
                        dispatcher.utter_message(text="Network error occurred. Please try again.")
                        return [
                            SlotSet("account_creation", "error"),
                            SlotSet("reached_clinic", "error")
                        ]
                    else:
                        dispatcher.utter_message(text="Invalid verification code. Please try again.")
                        return [
                            SlotSet("account_creation", "error"),
                            SlotSet("reached_clinic", "success")
                        ]
                    
            except Exception as e:
                logger.error(f"Exception verifying account: {str(e)}")
                dispatcher.utter_message(text="An error occurred while verifying your account. Please try again.")
                return [SlotSet("account_creation", "error"), SlotSet("reached_clinic", "error")]
        else:
            if not user_phone_number or not user_name:
                dispatcher.utter_message(text="Missing required information. Please provide your phone number and name.")
                return [SlotSet("account_creation", "error"), SlotSet("reached_clinic", "error"), SlotSet("missing_slots", "user_phone_number, user_name")]
    
            try:
                logger.info(f"Creating account for user {user_name} with phone {user_phone_number}")
                response = backend.create_account(
                    phone_number=user_phone_number,
                    user_name=user_name
                )
                
                if response.get("status") == "success":
                    return [SlotSet("account_creation", "initiated"), SlotSet("reached_clinic", "success")]
                else:
                    error_type = response.get("error_type")
                    error_message = response.get("message", "Unknown error")
                    logger.error(f"Account creation failed: {error_message}")
                    
                    if error_type == "user_exists":
                        dispatcher.utter_message(text="An account already exists with this phone number. Please try logging in.")
                        return [
                            SlotSet("account_creation", "error"),
                            SlotSet("user_exists", True),
                            SlotSet("reached_clinic", "success")
                        ]
                    elif error_type == "network_error":
                        return [
                            SlotSet("account_creation", "error"),
                            SlotSet("reached_clinic", "error")
                        ]
                    else:
                        dispatcher.utter_message(text="Failed to create account. Please try again.")
                        return [SlotSet("account_creation", "error"), SlotSet("reached_clinic", "success")]
                    
            except Exception as e:
                logger.error(f"Exception creating account: {str(e)}")
                dispatcher.utter_message(text="An error occurred while creating your account. Please try again.")
                return [SlotSet("account_creation", "error"), SlotSet("reached_clinic", "error")]

class ActionAddPaymentMethod(Action):
    def name(self) -> Text:
        return "action_add_payment_method"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        phone_number = tracker.get_slot("registered_phone_number") or tracker.get_slot("user_phone_number")
        card_number = tracker.get_slot("card_number")
        card_expiry_month = tracker.get_slot("card_expiry_month")
        card_expiry_year = tracker.get_slot("card_expiry_year")
        card_cvv = tracker.get_slot("card_cvv")
        
        logger.info(f"Adding payment method: Card ending in {card_number[-4:] if card_number else 'N/A'}")
        
        if not all([card_number, card_expiry_month, card_expiry_year, card_cvv]):
            dispatcher.utter_message(text="Missing required card information. Please provide all details.")
            return [SlotSet("payment_method", "missing_info")]
        
        if len(card_number) < 13 or len(card_number) > 19:
            dispatcher.utter_message(text="Invalid card number. Please check and try again.")
            return [SlotSet("payment_method", "invalid_card")]
            
        try:
            month = int(card_expiry_month)
            year = int(card_expiry_year)
            if month < 1 or month > 12:
                dispatcher.utter_message(text="Invalid expiry month. Please enter a number between 1 and 12.")
                return [SlotSet("payment_method", "invalid_expiry")]
        except ValueError:
            dispatcher.utter_message(text="Invalid expiry date format. Please enter valid numbers.")
            return [SlotSet("payment_method", "invalid_expiry")]
            
        if len(card_cvv) < 3 or len(card_cvv) > 4:
            dispatcher.utter_message(text="Invalid CVV. Please check and try again.")
            return [SlotSet("payment_method", "invalid_cvv")]
        
        try:
            response = backend.add_payment_method(
                phone_number=phone_number,
                card_number=card_number,
                card_expiry_month=card_expiry_month,
                card_expiry_year=card_expiry_year,
                card_cvv=card_cvv
            )
            
            if "error" in response:
                logger.error(f"Error from add payment method API: {response['error']}")
                return [SlotSet("payment_method", "error")]
                
            if response.get("status") == "success":
                return [SlotSet("payment_method", "success")]
            else:
                error_msg = response.get("message", "Unknown error")
                logger.error(f"Add payment method failed: {error_msg}")
                return [SlotSet("payment_method", "error")]
                
        except Exception as e:
            logger.error(f"Error adding payment method: {str(e)}")
            return [SlotSet("payment_method", "error")]

class ActionVerifyAccount(Action):
    def name(self) -> Text:
        return "action_verify_account"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        otp = tracker.get_slot("account_auth_otp_action")
        user_phone_number = tracker.get_slot("registered_phone_number")
        auth_initiated = tracker.get_slot("auth_initiated")
        
        logger.info(f"Verifying account for phone number {user_phone_number}")
        
        if not user_phone_number:
            dispatcher.utter_message(text="Missing required information. Please provide your phone number.")
            return [SlotSet("auth_initiated", "false")]
        
        if not auth_initiated:
            try:
                logger.info(f"Initiating account authentication for {user_phone_number}")
                response = backend.initiate_account_auth(phone_number=user_phone_number)
                
                if response.get("status") == "success":
                    return [
                        SlotSet("auth_initiated", True),
                        SlotSet("authentication_status", "pending"),
                        SlotSet("reached_clinic", "success")
                    ]
                else:
                    error_type = response.get("error_type")
                    error_message = response.get("message", "Unknown error")
                    logger.error(f"Account auth initiation failed: {error_message}")
                    
                    if error_type == "user_not_found":
                        return [
                            SlotSet("auth_initiated", False),
                            SlotSet("authentication_status", "error"),
                            SlotSet("reached_clinic", "success"),
                            SlotSet("user_not_found", "success")
                        ]
                    elif error_type == "network_error":
                        return [
                            SlotSet("reached_clinic", "error"),
                            SlotSet("authentication_status", "error"),
                            SlotSet("auth_initiated", False)
                        ]
                    else:
                        return [
                            SlotSet("auth_initiated", False),
                            SlotSet("authentication_status", "error"),
                            SlotSet("reached_clinic", "success")
                        ]
                        
            except Exception as e:
                logger.error(f"Unexpected error during account authentication: {e}")
                dispatcher.utter_message(text="An unexpected error occurred. Please try again later.")
                return [
                    SlotSet("reached_clinic", "error"),
                    SlotSet("authentication_status", "error"),
                    SlotSet("auth_initiated", False)
                ]
        else:
            if not otp:
                dispatcher.utter_message(text="Please provide the verification code sent to your phone.")
                return [SlotSet("return_value", "error")]
                
            try:
                logger.info(f"Verifying OTP for phone number {user_phone_number} with OTP {otp}")
                response = backend.verify_auth_otp(
                    phone_number=user_phone_number,
                    otp=otp
                )
                
                if response.get("status") == "success":
                    user_name = response.get("user_name")
                    payment_method = response.get("payment_method", [])
                    
                    card_number = payment_method[0] if len(payment_method) > 0 else ""
                    card_expiry_month = payment_method[1] if len(payment_method) > 1 else ""
                    card_expiry_year = payment_method[2] if len(payment_method) > 2 else ""
                    card_cvv = payment_method[3] if len(payment_method) > 3 else ""
                    
                    return [
                        SlotSet("authentication_status", "success"),
                        SlotSet("card_holder_name", user_name),
                        SlotSet("card_number", card_number),
                        SlotSet("card_expiry_month", card_expiry_month),
                        SlotSet("card_expiry_year", card_expiry_year),
                        SlotSet("card_cvv", card_cvv),
                        SlotSet("auth_initiated", "success"),
                        SlotSet("reached_clinic", "success"),
                        SlotSet("otp_status","success")
                    ]
                else:
                    error_message = response.get("message", "Invalid verification code")
                    error_type = response.get("error_type", "")
                    logger.error(f"Account auth verification failed: {error_message}")
                    
                    if error_type == "user_not_found" or "not found" in error_message.lower():
                        dispatcher.utter_message(text="We couldn't find an account with that phone number. Please check the number or create a new account.")
                    elif error_type == "invalid_otp":
                        return [
                            SlotSet("authentication_status", "error"),
                            SlotSet("reached_clinic", "success"),
                            SlotSet("otp_status","error")
                        ]
                    elif error_type == "network_error":
                        dispatcher.utter_message(text="Network error occurred. Please try again.")
                        return [
                            SlotSet("authentication_status", "error"),
                            SlotSet("reached_clinic", "error")
                        ]
                    else:
                        dispatcher.utter_message(text="Invalid verification code. Please try again.")
                        return [
                            SlotSet("authentication_status", "error"),
                            SlotSet("reached_clinic", "success")
                        ]
                    return [
                        SlotSet("authentication_status", "error"),
                        SlotSet("reached_clinic", "success" if error_type != "network_error" else "error")
                    ]
            except Exception as e:
                logger.error(f"Error verifying account authentication: {e}")
                dispatcher.utter_message(text="An error occurred during verification.")
                return [SlotSet("authentication_status", "error"), SlotSet("reached_clinic", "error")]

class ActionCheckAuthStatus(Action):
    def name(self) -> Text:
        return "action_check_auth_status"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        authentication_status = tracker.get_slot("authentication_status")
        if authentication_status == "pending":
            return [SlotSet("authentication_status", "pending")]
        else:
            return [SlotSet("authentication_status", "error")]

class ActionResendAuthOTP(Action):
    def name(self) -> Text:
        return "action_resend_auth_otp"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        dispatcher.utter_message(text="Resending OTP...")
        dispatcher.utter_message(text="OTP Resent Successfully.")
        return [] 