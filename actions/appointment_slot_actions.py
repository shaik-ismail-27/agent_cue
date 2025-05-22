from typing import Any, Dict, List, Text
import logging
from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher

from actions.backend_client import backend

# Set up logging
logger = logging.getLogger(__name__)

class ActionSuggestAlternativeTimeSlots(Action):
    def name(self) -> Text:
        return "action_suggest_alternative_time_slots"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        selected_clinic = tracker.get_slot("selected_clinic")
        appointment_date = tracker.get_slot("appointment_date")
        appointment_time = tracker.get_slot("appointment_time")
        
        if not all([selected_clinic, appointment_date, appointment_time]):
            logger.warning("Missing required slots for alternative time suggestions")
            dispatcher.utter_message(text="I need the clinic name, date, and time to find alternative slots.")
            return [SlotSet("get_alternative", "missing_info")]
        
        try:
            logger.info(f"Finding alternative slots for {appointment_date} at {appointment_time}")
            
            response = backend.get_nearest_available_slots(
                date=appointment_date,
                time=appointment_time,
                clinic=selected_clinic
            )
            
            if response.get("status") == "success":
                available_slots = response.get("available_slots", [])
                
                if not available_slots:
                    logger.info(f"No alternative slots found for {appointment_date}")
                    dispatcher.utter_message(text=f"Unfortunately, no alternative time slots are available on {appointment_date}. Please try a different date.")
                    return [SlotSet("get_alternative", "no_alternatives"), SlotSet("reached_clinic", "success")]
                
                time_slots = []
                slot_titles = {}

                for i, slot in enumerate(available_slots[:3], 1):
                    slot_time = slot.get("time", "")
                    date = slot.get("date", appointment_date)
                    formatted_date = date.split('T')[0] if 'T' in date else date
                    
                    time_slots.append((slot_time, formatted_date))
                    title_text = f"{slot_time} on {formatted_date}"
                    slot_titles[f"slot_{i}"] = title_text
                
                logger.info(f"Found {len(time_slots)} alternative slots")
                dispatcher.utter_message(
                    option_1_title=slot_titles.get("slot_1", "Currently Unavailable"),
                    option_2_title=slot_titles.get("slot_2", "Currently Unavailable"),
                    option_3_title=slot_titles.get("slot_3", "Currently Unavailable")
                )
                
                return [
                    SlotSet("get_alternative", "alternatives_found"),
                    SlotSet("appointment_time", None),
                    SlotSet("selected_option", None),
                    SlotSet("time_slots", time_slots),
                    SlotSet("option_1_title", slot_titles.get("slot_1", "Currently Unavailable")),
                    SlotSet("option_2_title", slot_titles.get("slot_2", "Currently Unavailable")),
                    SlotSet("option_3_title", slot_titles.get("slot_3", "Currently Unavailable")),
                    SlotSet("reached_clinic", "success")
                ]
            else:
                error_type = response.get("error_type", "")
                error_message = response.get("message", "Unknown error")
                logger.error(f"Finding alternative slots failed: {error_message}")
                
                if error_type == "clinic_unavailable":
                    dispatcher.utter_message(text="Sorry, the clinic is currently unavailable. Please try again later or choose a different clinic.")
                    return [
                        SlotSet("get_alternative", "error"),
                        SlotSet("reached_clinic", "error"),
                        SlotSet("selected_clinic", None)
                    ]
                elif error_type == "network_error":
                    dispatcher.utter_message(text="Network error occurred. Please try again.")
                    return [
                        SlotSet("get_alternative", "error"),
                        SlotSet("reached_clinic", "error")
                    ]
                else:
                    dispatcher.utter_message(text="Sorry, I couldn't find alternative time slots. Please try a different time or date.")
                    return [
                        SlotSet("get_alternative", "error"),
                        SlotSet("reached_clinic", "success")
                    ]
                
        except Exception as e:
            logger.error(f"Error finding alternative time slots: {str(e)}")
            dispatcher.utter_message(text="An unexpected error occurred. Please try again.")
            return [
                SlotSet("get_alternative", "error"),
                SlotSet("reached_clinic", "error")
            ]

class ActionProcessSelectedSlot(Action):
    def name(self) -> Text:
        return "action_process_selected_slot"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        selected_option = tracker.get_slot("selected_option")
        
        if not selected_option:
            dispatcher.utter_message(text="Please select one of the time options.")
            return [SlotSet("is_available", "no_selection")]
        
        time_slots = tracker.get_slot("time_slots")
        
        if isinstance(selected_option, str):
            selected_option = selected_option.strip("'\"")
        
        if not time_slots or not isinstance(time_slots, list) or len(time_slots) < int(selected_option):
            dispatcher.utter_message(text="There was an error with your selection. Please try again.")
            return [SlotSet("is_available", "invalid_option")]
        
        index = int(selected_option) - 1
        selected_time, selected_date = time_slots[index]
        
        logger.info(f"User selected option {selected_option} with time {selected_time} on {selected_date}")
        
        dispatcher.utter_message(text=f"You've selected {selected_time} on {selected_date}. Checking availability...")
            
        return [
            SlotSet("is_available", "time_selected"),
            SlotSet("appointment_time", selected_time),
            SlotSet("appointment_date", selected_date),
            SlotSet("date_time_finalized", True)
        ]

class ActionCheckAppointmentSlot(Action):
    def name(self) -> str:
        return "action_check_appointment_slot"

    def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[str, Any]
    ) -> List[Dict[Text, Any]]:
        clinic_name = tracker.get_slot("selected_clinic")
        date = tracker.get_slot("appointment_date")
        time = tracker.get_slot("appointment_time")
        specialization = tracker.get_slot("specialized_service")
        
        logger.info(f"Checking availability for {clinic_name} on {date} at {time}")
        
        if not all([clinic_name, date, time]):
            dispatcher.utter_message(text="I need the clinic name, date, and time to check appointment availability.")
            return [SlotSet("return_value", "missing_info")]
        
        if time and not any(period in time.upper() for period in ['AM', 'PM']):
            time = f"{time} AM"
            logger.info(f"Added default AM to time: {time}")
            return [SlotSet("appointment_time", time)]
        
        available_slots = tracker.get_slot("available_slots")
        return_value = tracker.get_slot("return_value") or ""
        
        if available_slots and return_value == "alternatives_found":
            time_normalized = time.strip()
            
            logger.info(f"Validating time {time_normalized} against available slots: {available_slots}")
            
            if time_normalized not in available_slots:
                match_found = False
                for slot in available_slots:
                    if time_normalized.lower() in slot.lower() or slot.lower() in time_normalized.lower():
                        logger.info(f"Found close match: {slot} for input: {time_normalized}")
                        time = slot
                        match_found = True
                        break
                
                if not match_found:
                    available_slots_text = ", ".join(available_slots)
                    dispatcher.utter_message(
                        text=f"Sorry, '{time}' is not one of the available time slots. Please select one of: {available_slots_text}"
                    )
                    return [SlotSet("is_available", "invalid_selection")]
        
        response = backend.check_availability(
            clinic_id=clinic_name,
            date=date,
            time=time,
            specialization=specialization or ""
        )
        
        if "error" in response:
            logger.error(f"Error checking appointment availability: {response['error']}")
            return [SlotSet("is_available", "error")]
        
        if response.get("is_available", False):
            if "doctor" in response:
                doctor = response["doctor"]
                dispatcher.utter_message(text=f"Great news! The slot on {date} at {time} is available with {doctor['name']} ({doctor['specialization']}).")
            else:
                dispatcher.utter_message(text=f"Great news! The slot on {date} at {time} is available.")
            
            return [
                SlotSet("is_available", "available"),
                SlotSet("available_slots", None),
                SlotSet("appointment_time", time),
                SlotSet("return_value", None)
            ]
        else:
            return [SlotSet("is_available", "unavailable")] 