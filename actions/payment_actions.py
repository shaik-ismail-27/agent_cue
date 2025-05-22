from typing import Any, Dict, List, Text
import logging
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from actions.backend_client import backend

# Set up logging
logger = logging.getLogger(__name__)

class ActionCheckAccountPaymentMethodNeeded(Action):
    def name(self) -> Text:
        return "action_check_account_payment_method_needed"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        selected_clinic = tracker.get_slot("selected_clinic")
        payment_required = tracker.get_slot("payment_required")
        
        logger.info(f"ActionCheckPaymentRequired called with selected_clinic: {selected_clinic}")
        
        if payment_required is not None:
            return [SlotSet("payment_required", payment_required)]
        
        try:
            response = backend.check_payment_required(clinic_name=selected_clinic)
            
            if "error" in response:
                logger.error(f"Error checking if payment is required: {response['error']}")
                return [SlotSet("payment_required", False)]
            
            payment_required = response.get("requires_payment", False)
            logger.info(f"Payment required for clinic '{selected_clinic}': {payment_required}")
            
            return [SlotSet("payment_required", payment_required)]
        except Exception as e:
            logger.error(f"Exception checking payment requirements: {str(e)}")
            return [SlotSet("payment_required", False)]

class ActionCheckBookingPaymentRequirement(Action):
    def name(self) -> Text:
        return "action_check_booking_payment_requirement"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        selected_clinic = tracker.get_slot("selected_clinic")
        clinic_fee = tracker.get_slot("clinic_fee")
        
        logger.info(f"Checking payment requirement for clinic '{selected_clinic}' with fee: {clinic_fee}")
        
        if clinic_fee is None:
            logger.info(f"No clinic fee information available for '{selected_clinic}', defaulting to payment required")
            return [SlotSet("booking_payment_requirement", True)]
        
        if clinic_fee == 0:
            logger.info(f"Clinic '{selected_clinic}' has fee of 0, payment NOT required")
            return [SlotSet("booking_payment_requirement", False)]
                
        logger.info(f"Clinic '{selected_clinic}' has fee of {clinic_fee}, payment IS required")
        return [SlotSet("booking_payment_requirement", True)]

class ActionSendPaymentRequest(Action):
    def name(self) -> str:
        return "action_send_payment_request"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]
    ) -> List[Dict[Text, Any]]:
        selected_clinic = tracker.get_slot("selected_clinic") or tracker.get_slot("booking_clinic")
        phone_number = tracker.get_slot("registered_phone_number") or tracker.get_slot("user_phone_number")
        
        logger.info(f"Processing payment for user with phone: {phone_number} at clinic: {selected_clinic}")
        
        # Get all required payment information
        phone_number = tracker.get_slot("registered_phone_number") or tracker.get_slot("user_phone_number")
        clinic_name = tracker.get_slot("selected_clinic")
        specialization = tracker.get_slot("specialized_service")
        card_holder_name = tracker.get_slot("card_holder_name")
        card_number = tracker.get_slot("card_number")
        card_expiry_month = tracker.get_slot("card_expiry_month")
        card_expiry_year = tracker.get_slot("card_expiry_year")
        card_cvv = tracker.get_slot("card_cvv")
        amount = 50.00
        currency = "INR"

        # Validate required fields
        if not all([phone_number, clinic_name, card_holder_name, card_number, 
                   card_expiry_month, card_expiry_year, card_cvv]):
            dispatcher.utter_message(text="Missing required payment information. Please provide all card details.")
            return [
                SlotSet("request_payment", "error"),
                SlotSet("reached_clinic", "error"),
                SlotSet("missing_slots", "card_details")
            ]

        try:
            response = backend.initiate_payment(
                phone_number=phone_number,
                clinic_name=clinic_name,
                specialization=specialization,
                card_number=card_number,
                card_expiry_month=card_expiry_month,
                card_expiry_year=card_expiry_year,
                card_holder_name=card_holder_name,
                card_cvv=card_cvv,
                amount=amount,
                currency=currency
            )

            if response.get("status") == "success":
                return [
                    SlotSet("request_payment", "success"),
                    SlotSet("payment_amount", amount),
                    SlotSet("transaction_id", response.get("transaction_id")),
                    SlotSet("reached_clinic", "success")
                ]
            else:
                error_type = response.get("error_type", "")
                error_message = response.get("message", "Unknown error")
                logger.error(f"Payment request failed: {error_message}")
                
                if error_type == "invalid_card":
                    dispatcher.utter_message(text="Invalid card details. Please check and try again.")
                    return [
                        SlotSet("request_payment", "error"),
                        SlotSet("reached_clinic", "success")
                    ]
                elif error_type == "insufficient_funds":
                    dispatcher.utter_message(text="Insufficient funds in your account. Please try with a different card.")
                    return [
                        SlotSet("request_payment", "error"),
                        SlotSet("reached_clinic", "success")
                    ]
                elif error_type == "network_error":
                    dispatcher.utter_message(text="Network error occurred. Please try again.")
                    return [
                        SlotSet("request_payment", "error"),
                        SlotSet("reached_clinic", "error")
                    ]
                else:
                    dispatcher.utter_message(text="Payment processing failed. Please try again.")
                    return [
                        SlotSet("request_payment", "error"),
                        SlotSet("reached_clinic", "success")
                    ]

        except Exception as e:
            logger.error(f"Exception processing payment: {str(e)}")
            dispatcher.utter_message(text="An error occurred while processing your payment. Please try again.")
            return [
                SlotSet("request_payment", "error"),
                SlotSet("reached_clinic", "error")
            ]

class ActionVerifyPaymentOTP(Action):
    def name(self) -> Text:
        return "action_verify_payment_otp"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        phone_number = tracker.get_slot("registered_phone_number") or tracker.get_slot("user_phone_number")
        otp = tracker.get_slot("payment_otp")
        transaction_id = tracker.get_slot("transaction_id")
        amount = tracker.get_slot("clinic_fee")
        
        # Validate required fields
        if not all([phone_number, otp, transaction_id]):
            dispatcher.utter_message(text="Missing required information. Please provide the OTP and ensure you have a valid transaction.")
            return [
                SlotSet("payment_status", "error"),
                SlotSet("missing_slots", "payment_otp, transaction_id")
            ]
        
        try:
            response = backend.verify_payment_otp(
                phone_number=phone_number,
                otp=otp,
                transaction_id=transaction_id
            )

            if response.get("status") == "success":
                transaction_id = response.get("transaction_id")
                card_type = response.get("card_type")
                card_last4 = response.get("card_last4")
                
                dispatcher.utter_message(
                    text=f"Payment processed successfully!\n"
                    f"Amount: ₹{amount}\n"
                    f"Transaction ID: {transaction_id}"
                )

                return [
                    SlotSet("payment_status", "success"),
                    SlotSet("transaction_id", transaction_id),
                    SlotSet("payment_amount", amount),
                    SlotSet("payment_card_type", card_type),
                    SlotSet("payment_card_last4", card_last4)
                ]
            else:
                error_type = response.get("error_type", "")
                error_message = response.get("message", "Unknown error")
                logger.error(f"Payment OTP verification failed: {error_message}")
                
                if error_type == "invalid_otp":
                    return [
                        SlotSet("payment_status", "error"),
                        SlotSet("payment_otp", None),
                        SlotSet("otp_status","invalid")
                    ]
                elif error_type == "expired_otp":
                    dispatcher.utter_message(text="OTP has expired. Please request a new OTP.")
                    return [
                        SlotSet("payment_status", "error"),
                        SlotSet("payment_otp", None),
                        SlotSet("otp_status","invalid")
                    ]
                elif error_type == "transaction_expired":
                    dispatcher.utter_message(text="Transaction has expired. Please initiate a new payment.")
                    return [
                        SlotSet("payment_status", "error"),
                        SlotSet("transaction_id", None)
                    ]
                elif error_type == "network_error":
                    dispatcher.utter_message(text="Network error occurred. Please try again.")
                    return [
                        SlotSet("payment_status", "error"),
                        SlotSet("reached_clinic", "error")
                    ]
                else:
                    dispatcher.utter_message(text="Payment verification failed. Please try again.")
                    return [SlotSet("payment_status", "error")]
                
        except Exception as e:
            logger.error(f"Exception verifying payment OTP: {str(e)}")
            dispatcher.utter_message(text="An error occurred while verifying your payment. Please try again.")
            return [
                SlotSet("payment_status", "error"),
                SlotSet("reached_clinic", "error")
            ]

class ActionCheckPaymentStatus(Action):
    def name(self) -> Text:
        return "action_check_payment_status"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        payment_status = tracker.get_slot("payment_status")
        
        logger.info(f"Checking payment status: {payment_status}")
        
        if payment_status == "success":
            return [SlotSet("payment_status", "success")]
        elif payment_status == "failed":
            dispatcher.utter_message(text="There was an issue with your payment. Please try again.")
            return [SlotSet("payment_status", "failed")]
        else:
            dispatcher.utter_message(text="Your payment is still being processed.")
            return [SlotSet("payment_status", "pending")] 