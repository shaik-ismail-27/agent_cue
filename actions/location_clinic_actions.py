from typing import Any, Dict, List, Text
import logging
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
import re

# Set up logging
logger = logging.getLogger(__name__)

class ActionSetCityState(Action):
    def name(self) -> Text:
        return "action_set_city_state"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            location = tracker.get_slot("location")
            if not location:
                logger.error("Location slot is empty")
                dispatcher.utter_message(text="Please provide a location so I can find services near you.")
                return [SlotSet("city", None), SlotSet("state", None)]
                
            parts = location.split(",")
            if len(parts) < 2:
                logger.warning(f"Location format incorrect: {location}")
                dispatcher.utter_message(text="I couldn't understand the location format. Please provide it as 'City, State' (e.g., 'Austin, Texas').")
                return [SlotSet("city", None), SlotSet("state", None)]
                
            city = parts[0].strip()
            state = parts[1].strip()
            
            logger.info(f"Successfully extracted city: {city}, state: {state} from location: {location}")
            return [SlotSet("city", city), SlotSet("state", state)]
        except Exception as e:
            logger.error(f"Error parsing location: {str(e)}")
            dispatcher.utter_message(text="I couldn't resolve the location into city and state. Let's go step by step.")
            return [SlotSet("city", None), SlotSet("state", None)]

class ActionValidateClinicSelection(Action):
    def name(self) -> Text:
        return "action_validate_clinic_selection"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        selected_clinic = tracker.get_slot("selected_clinic")
        displayed_clinics = tracker.get_slot("displayed_clinics")
        clinics_fees = tracker.get_slot("clinics_fees")
        
        logger.info(f"Validating clinic selection: '{selected_clinic}' against displayed clinics: {displayed_clinics}")
        logger.info(f"Available clinic fees: {clinics_fees}")
        
        if not selected_clinic or not displayed_clinics:
            return []
        
        clinic_fee = None
        real_clinic_name = None
        
        if selected_clinic.isdigit():
            try:
                index = int(selected_clinic) - 1
                
                if 0 <= index < len(displayed_clinics):
                    real_clinic_name = displayed_clinics[index]
                    logger.info(f"Mapped numeric selection '{selected_clinic}' to clinic name: '{real_clinic_name}'")
                    
                    if clinics_fees and isinstance(clinics_fees, list) and 0 <= index < len(clinics_fees):
                        clinic_fee = clinics_fees[index]
                        logger.info(f"Found fee '{clinic_fee}' for clinic '{real_clinic_name}'")
                    
                    events = [SlotSet("selected_clinic", real_clinic_name)]
                    if clinic_fee is not None:
                        events.append(SlotSet("clinic_fee", clinic_fee))
                        events.append(SlotSet("invalid_clinic", False))
                    
                    return events
                else:
                    logger.error(f"Clinic selection out of range: {selected_clinic}, valid range is 1-{len(displayed_clinics)}")
                    return [SlotSet("invalid_clinic_number", True),]
            except Exception as e:
                logger.error(f"Error validating clinic selection: {str(e)}")
                return []
        
        if displayed_clinics and clinics_fees:
            for i, clinic_name in enumerate(displayed_clinics):
                if clinic_name.lower() == selected_clinic.lower():
                    if i < len(clinics_fees):
                        clinic_fee = clinics_fees[i]
                        logger.info(f"Found fee '{clinic_fee}' for clinic '{clinic_name}'")
                        return [SlotSet("clinic_fee", clinic_fee), SlotSet("invalid_clinic", False)]
            
            # If we get here, no matching clinic was found
            logger.error(f"Invalid clinic name entered: '{selected_clinic}'. Available clinics: {displayed_clinics}")
            return [SlotSet("invalid_clinic_name", True)]
        
        return []

class ActionValidateAppointmentDate(Action):
    def name(self) -> Text:
        return "action_validate_appointment_date"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        appointment_date = tracker.get_slot("appointment_date")
        
        if not appointment_date:
            return []
        
        logger.info(f"Validating appointment date: {appointment_date}")
        
        try:
            if re.match(r'^\d{2}-\d{2}-\d{4}$', appointment_date):
                logger.info(f"Date is in DD-MM-YYYY format: {appointment_date}")
                return []
            else:
                dispatcher.utter_message(text="Please enter a valid date in DD-MM-YYYY format (e.g., 05-04-2025)")
                return [SlotSet("appointment_date", None)]
                
        except Exception as e:
            logger.error(f"Error validating appointment date: {str(e)}")
            dispatcher.utter_message(text="Sorry, I couldn't process that date. Please use the format DD-MM-YYYY.")
            return [SlotSet("appointment_date", None)] 