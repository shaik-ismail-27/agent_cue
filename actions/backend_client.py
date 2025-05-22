import requests
from requests.exceptions import HTTPError, RequestException
from typing import Dict, List, Optional, Any, Tuple
import os
import logging

logger = logging.getLogger(__name__)

# Get the backend URL from environment variable or use default
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8002')

class BackendClient:
    @staticmethod
    def _process_response(response: requests.Response) -> Tuple[Dict[str, Any], Optional[str]]:
        """Process the response and return the data and error message if any."""
        try:
            data = response.json()
            # Check for error status in successful responses
            if data.get("status") == "error":
                error_message = data.get("message", "").lower()
                error_type = data.get("error_type", "")
                if error_type:
                    return data, error_type
                elif "appointment time is not available" in error_message:
                    return {"status": "error", "message": "Appointment time is not available"}, "slot_unavailable"
                elif "invalid otp" in error_message or "invalid verification code" in error_message:
                    return {"status": "error", "message": "Invalid OTP"}, "invalid_otp"
                elif "user not found" in error_message or "account not found" in error_message:
                    return {"status": "error", "message": "User not found"}, "user_not_found"
                elif "already exists" in error_message or "already registered" in error_message:
                    return {"status": "error", "message": "User already exists"}, "user_exists"
                return data, "unknown_error"
            return data, None
        except ValueError:
            return {"error": "Invalid JSON response"}, response.text

    @staticmethod
    def _handle_http_error(error: HTTPError) -> Tuple[Dict[str, Any], Optional[str]]:
        """Handle HTTP errors and return appropriate response."""
        status_code = error.response.status_code
        error_message = ""

        try:
            error_data = error.response.json()
            error_message = error_data.get("message", "").lower()
        except ValueError:
            error_message = error.response.text.lower()

        if status_code == 404:
            if "user not found" in error_message or "account not found" in error_message:
                return {"status": "error", "message": "User not found"}, "user_not_found"
            return {"status": "error", "message": "Resource not found"}, "not_found"
        elif status_code == 409:
            if "appointment time is not available" in error_message:
                return {"status": "error", "message": "Appointment time is not available"}, "slot_unavailable"
            elif "already exists" in error_message or "already registered" in error_message:
                return {"status": "error", "message": "User already exists"}, "user_exists"
            return {"status": "error", "message": "Resource conflict"}, "conflict"
        elif status_code == 400:
            if "invalid otp" in error_message or "invalid verification code" in error_message:
                return {"status": "error", "message": "Invalid OTP"}, "invalid_otp"
            return {"status": "error", "message": str(error)}, "bad_request"
        
        return {"status": "error", "message": str(error)}, "http_error"

    @staticmethod
    def get(endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generic GET request to the backend."""
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", params=params, timeout=10)
            response.raise_for_status()
            
            data, error = BackendClient._process_response(response)
            if error:
                return {"status": "error", "message": error, "error_type": "invalid_response"}
            
            return data

        except HTTPError as http_err:
            data, error_type = BackendClient._handle_http_error(http_err)
            data["error_type"] = error_type
            return data

        except RequestException as e:
            logger.error(f"Network error during GET request to {endpoint}: {e}")
            return {
                "status": "error",
                "message": "Unable to connect to the service",
                "error_type": "network_error"
            }

        except Exception as e:
            logger.error(f"Unexpected error during GET request to {endpoint}: {e}")
            return {
                "status": "error",
                "message": "An unexpected error occurred",
                "error_type": "unexpected_error"
            }

    @staticmethod
    def post(endpoint: str, json: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generic POST request to the backend."""
        try:
            full_url = f"{BACKEND_URL}{endpoint}"
            logger.info(f"Making POST request to: {full_url}")
            logger.info(f"With payload: {json}")
            
            response = requests.post(full_url, json=json, timeout=10)
            response.raise_for_status()
            
            data, error = BackendClient._process_response(response)
            if error:
                return {"status": "error", "message": error, "error_type": "invalid_response"}
            
            return data

        except HTTPError as http_err:
            data, error_type = BackendClient._handle_http_error(http_err)
            data["error_type"] = error_type
            return data

        except RequestException as e:
            logger.error(f"Network error during POST request to {endpoint}: {e}")
            return {
                "status": "error",
                "message": "Unable to connect to the service",
                "error_type": "network_error"
            }

        except Exception as e:
            logger.error(f"Unexpected error during POST request to {endpoint}: {e}")
            return {
                "status": "error",
                "message": "An unexpected error occurred",
                "error_type": "unexpected_error"
            }

    @staticmethod
    def get_clinics(city: str = None, state: str = None, type: str = None) -> Dict[str, Any]:
        """Get clinics from the backend server."""
        params = {}
        if city and state:
            params['location'] = f"{city} {state}"
        if type:
            params['type'] = type
            
        return BackendClient.get("/get_clinics", params=params)

    @staticmethod
    def create_account(phone_number: str, user_name: str) -> Dict[str, Any]:
        """Create a new user account and send OTP for verification."""
        return BackendClient.post(
            "/create_account",
            json={
                "phone_number": phone_number,
                "user_name": user_name
            }
        )
        
    @staticmethod
    def verify_account(phone_number: str, otp: str) -> Dict[str, Any]:
        """Verify a new account using OTP."""
        return BackendClient.post(
            "/verify_account_creation_otp",
            json={
                "phone_number": phone_number,
                "otp": otp
            }
        )

    @staticmethod
    def check_availability(clinic_id: str, date: str, time: str, specialization: str = '') -> Dict[str, Any]:
        """Check appointment slot availability."""
        params = {
            'clinic': clinic_id,
            'date': date,
            'time': time,
            'specialization': specialization
        }
        return BackendClient.get("/check_clinics_availability", params=params)

    @staticmethod
    def book_appointment(appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Book an appointment."""
        return BackendClient.post("/book_appointment", json=appointment_data)

    @staticmethod
    def initiate_account_auth(phone_number: str) -> Dict[str, Any]:
        """Initiate account authentication with OTP."""
        return BackendClient.post(
            "/initiate_account_auth",
            json={"phone_number": phone_number}
        )

    @staticmethod
    def verify_auth_otp(phone_number: str, otp: str) -> Dict[str, Any]:
        """Verify OTP for account authentication."""
        return BackendClient.post(
            "/verify_auth_otp",
            json={
                'phone_number': phone_number,
                'otp': otp
            }
        )

    @staticmethod
    def check_payment_required(clinic_name: str) -> Dict[str, Any]:
        """Check if payment is required for a clinic."""
        params = {'clinic_name': clinic_name}
        return BackendClient.get("/check_payment_required", params=params)

    @staticmethod
    def get_nearest_available_slots(date: str, time: str, clinic: str) -> Dict[str, Any]:
        """Get nearest available slots for a clinic from the backend server."""
        params = {
            'date': date,
            'time': time,
            'clinic': clinic
        }
        return BackendClient.get("/get_nearest_available_slots", params=params)

    @staticmethod
    def add_payment_method(phone_number: str, card_number: str, card_expiry_month: str, 
                          card_expiry_year: str, card_cvv: str) -> Dict[str, Any]:
        """Add a payment method for a user."""
        return BackendClient.post(
            "/add_payment_method", 
            json={
                "phone_number": phone_number,
                "card_number": card_number,
                "card_expiry_month": card_expiry_month,
                "card_expiry_year": card_expiry_year,
                "card_cvv": card_cvv
            }
        )

    @staticmethod
    def initiate_payment(phone_number: str, clinic_name: str, specialization: str = None,
                        card_number: str = None, card_expiry_month: str = None, 
                        card_expiry_year: str = None, card_holder_name: str = None,
                        card_cvv: str = None, amount: float = None, 
                        currency: str = "USD") -> Dict[str, Any]:
        """Initiate a payment transaction."""
        return BackendClient.post(
            "/initiate_payment",
            json={
                "phone_number": phone_number,
                "clinic_name": clinic_name,
                "specialization": specialization,
                "card_number": card_number,
                "card_expiry_month": card_expiry_month,
                "card_expiry_year": card_expiry_year,
                "card_holder_name": card_holder_name,
                "card_cvv": card_cvv,
                "amount": amount,
                "currency": currency
            }
        )
        
    @staticmethod
    def verify_payment_otp(phone_number: str, otp: str, transaction_id: str) -> Dict[str, Any]:
        """Verify OTP to complete a payment transaction."""
        return BackendClient.post(
            "/verify_payment_otp",
            json={
                "phone_number": phone_number,
                "otp": otp,
                "transaction_id": transaction_id
            }
        )

# Create a singleton instance
backend = BackendClient() 