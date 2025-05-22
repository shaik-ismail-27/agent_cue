from typing import Any, Dict, List, Text
import logging

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet, AllSlotsReset
from rasa_sdk.executor import CollectingDispatcher

from actions.backend_client import backend

# Set up logging
logger = logging.getLogger(__name__)


class ActionRecommendSpecialistClinics(Action):
    def name(self) -> str:
        return "action_recommend_specialist_clinics"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]
    ) -> List[Dict[Text, Any]]:
        city = tracker.get_slot("city")
        state = tracker.get_slot("state")
        specialized_service = tracker.get_slot("specialized_service")
        
        # Validate required fields
        if not all([city, state, specialized_service]):
            dispatcher.utter_message(text="I need both your location and the specialized service you're looking for.")
            return [
                SlotSet("clinic_recommendation_status", "missing_info"),
                SlotSet("missing_slots", "city, state, specialized_service")
            ]
        
        try:
            # Get clinics from backend with specialization
            response = backend.get_clinics(
                city=city,
                state=state,
                type=specialized_service
            )
            
            if response.get("status") == "success":
                # Get matching clinics
                matching_clinics = response.get("clinics", [])
                
                if not matching_clinics:
                    dispatcher.utter_message(text=f"I couldn't find any clinics offering {specialized_service} in {city}, {state}.")
                    return [SlotSet("clinic_recommendation_status", "no_match")]
                
                # Format the clinics list for display
                clinics_list = ""
                displayed_clinics = []  # To store the names of displayed clinics
                clinics_fees = []  # To store the fees of displayed clinics
                
                # Only show the top 3 clinics
                shown_clinics = matching_clinics[:3]
                
                for idx, clinic in enumerate(shown_clinics, 1):
                    clinics_list += f"{idx}. {clinic['name']}\n"
                    clinics_list += f"   Rating: {clinic['rating']} ⭐\n"
                    clinics_list += f"   Address: {clinic['address']}\n"
                    clinics_list += f"   Hours: {clinic['hours']}\n"
                    clinics_list += f"   Services: {', '.join(clinic['services'][:3])}...\n"
                    clinics_list += f"   Waiting Time: {clinic['waiting_time']}\n"
                    
                    # Check if clinic requires payment or if the service is free
                    clinic_fee = 0
                    if not clinic.get('requires_payment', True) or (specialized_service in clinic.get('price_list', {}) and clinic['price_list'].get(specialized_service, 0) == 0):
                        clinics_list += f"   Price: Free (No payment required)\n\n"
                    else:
                        # Find a matching price in the price list
                        price = "Not specified"
                        price_list = clinic.get('price_list', {})
                        
                        # First try direct match
                        if specialized_service in price_list:
                            price = price_list[specialized_service]
                            clinic_fee = price
                        else:
                            # Try case-insensitive partial match
                            specialized_service_lower = specialized_service.lower()
                            for key, value in price_list.items():
                                if specialized_service_lower in key.lower():
                                    price = value
                                    clinic_fee = value
                                    break
                        
                        # If still not found and the clinic requires payment, show a default price
                        if price == "Not specified" and clinic.get('requires_payment', True):
                            price = "₹175 - ₹250 (estimated)"
                            clinic_fee = 200  # Estimated average fee
                        
                        clinics_list += f"   Price: {price}\n\n"
                    
                    displayed_clinics.append(clinic['name'])  # Add clinic name to the list
                    clinics_fees.append(clinic_fee)  # Store the fee for this clinic
                
                dispatcher.utter_message(text=f"I found these clinics offering {specialized_service} in {city}, {state}:\n\n{clinics_list}")
                
                # Return slots including displayed clinics and their fees for mapping later
                return [
                    SlotSet("clinic_recommendation_status", "success"),
                    SlotSet("displayed_clinics", displayed_clinics),
                    SlotSet("clinics_fees", clinics_fees)
                ]
            else:
                error_type = response.get("error_type", "")
                error_message = response.get("message", "Unknown error")
                logger.error(f"Specialist clinic recommendation failed: {error_message}")
                
                if error_type == "location_not_found":
                    dispatcher.utter_message(text=f"I couldn't find any clinics in {city}, {state}. Please check the location and try again.")
                    return [
                        SlotSet("clinic_recommendation_status", "clinic_at_location_not_found"),
                        SlotSet("reached_clinic", "error")
                    ]
                elif error_type == "service_not_available":
                    dispatcher.utter_message(text=f"The specialized service '{specialized_service}' is not available in {city}, {state}.")
                    return [
                        SlotSet("clinic_recommendation_status", "service_not_available"),
                        SlotSet("reached_clinic", "success")
                    ]
                elif error_type == "network_error":
                    dispatcher.utter_message(text="Network error occurred. Please try again.")
                    return [
                        SlotSet("clinic_recommendation_status", "error"),
                        SlotSet("reached_clinic", "error")
                    ]
                else:
                    dispatcher.utter_message(text="Sorry, I'm having trouble finding specialized clinics. Please try again.")
                    return [
                        SlotSet("clinic_recommendation_status", "error"),
                        SlotSet("reached_clinic", "success")
                    ]
                
        except Exception as e:
            logger.error(f"Exception recommending specialist clinics: {str(e)}")
            dispatcher.utter_message(text="An error occurred while searching for specialized clinics. Please try again.")
            return [
                SlotSet("clinic_recommendation_status", "error"),
                SlotSet("reached_clinic", "error")
            ]



class ActionBookSpecialistAppointment(Action):
    def name(self) -> str:
        return "action_book_specialist_appointment"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]
    ) -> List[Dict[Text, Any]]:
        required_slots = [
            "selected_clinic",
            "appointment_date",
            "appointment_time",
            "patient_name",
            "patient_age",
            "specialized_service"
        ]
        
        # Get the slot values without any auto-filling
        slots = {slot: tracker.get_slot(slot) for slot in required_slots}
        
        # Check for missing slots
        missing_slots = [slot for slot, value in slots.items() if not value]
        
        if missing_slots:
            dispatcher.utter_message(text=f"Missing required information: {', '.join(missing_slots)}")
            return [
                SlotSet("booking_status", "missing_info"),
                SlotSet("missing_slots", ", ".join(missing_slots))
            ]
        
        try:            
            # Book appointment
            appointment_data = {
                "clinic": slots["selected_clinic"],
                "date": slots["appointment_date"],
                "time": slots["appointment_time"],
                "patient_name": slots["patient_name"],
                "patient_age": slots["patient_age"],
                "specialization": slots["specialized_service"]
            }
            
            # Add phone number if available
            phone_number = tracker.get_slot("phone_number") or tracker.get_slot("user_phone_number")
            if phone_number:
                appointment_data["phone_number"] = phone_number
            
            logger.info(f"Booking specialist appointment with data: {appointment_data}")
            response = backend.book_appointment(appointment_data)
            
            if response.get("status") == "success":
                appointment_id = response.get("appointment_id")
                doctor = response.get("doctor", {})
                
                # Format success message
                message = (
                    f"Great! Your specialized appointment has been booked successfully.\n"
                    f"Appointment ID: {appointment_id}\n"
                    f"Patient Name: {slots['patient_name']}\n"
                )
                
                if doctor:
                    message += f"Doctor: {doctor.get('name')} ({doctor.get('specialization')})\n"
                
                message += (
                    f"Clinic: {appointment_data['clinic']}\n"
                    f"Service: {appointment_data['specialization']}\n"
                    f"Date: {slots['appointment_date']}\n"
                    f"Time: {appointment_data['time']}"
                )
                
                dispatcher.utter_message(text=message)
                return [SlotSet("booking_status", "success"), SlotSet("reached_clinic", "success")]
            else:
                error_type = response.get("error_type", "")
                error_message = response.get("message", "Unknown error")
                logger.error(f"Specialist appointment booking failed: {error_message}")
                
                if error_type == "slot_unavailable":
                    dispatcher.utter_message(text="Sorry, this appointment slot is no longer available. Please choose a different time.")
                    return [
                        SlotSet("booking_status", "failed"),
                        SlotSet("appointment_time", None),
                        SlotSet("rescheduling_reason", True),
                        SlotSet("reached_clinic", "success")
                    ]
                elif error_type == "clinic_unavailable":
                    dispatcher.utter_message(text="Sorry, the clinic is currently unavailable. Please try again later or choose a different clinic.")
                    return [
                        SlotSet("booking_status", "failed"),
                        SlotSet("selected_clinic", None),
                    ]
                elif error_type == "network_error":
                    dispatcher.utter_message(text="Network error occurred. Please try again.")
                    return [
                        SlotSet("booking_status", "failed"),
                        SlotSet("reached_clinic", "error")
                    ]
                else:
                    return [SlotSet("booking_status", "failed"),SlotSet("reached_clinic", "success"),SlotSet("appointment_date", None),SlotSet("appointment_time", None),SlotSet("rescheduling_reason", True)]
                
        except Exception as e:
            logger.error(f"Exception booking specialist appointment: {str(e)}")
            dispatcher.utter_message(text="An error occurred while booking your appointment. Please try again.")
            return [
                SlotSet("booking_status", "error"),
                SlotSet("reached_clinic", "error")
            ]
        