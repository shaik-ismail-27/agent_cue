from flask import Flask, jsonify, request
import logging
import random
import time
from datetime import datetime
import uuid
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock registered users data
registered_users = {
    "+1 234-567-8910": {
        "user_name": "bob alex",
        "payment_method": [
            {
                "id": "pm_1",
                "type": "debit_card",
                "last4": "9876",
                "brand": "Mastercard",
                "exp_month": 8,
                "exp_year": 2024,
                "card_number": "1234567890123456",
                "card_cvv": "342"
            }
        ]
    },
    "+91 1234567890": {
        "user_name": "rahan khan",
        "payment_method": [
            {
                "id": "pm_1",
                "type": "debit_card",
                "last4": "4321",
                "brand": "Visa",
                "exp_month": 12,
                "exp_year": 2025,
                "card_number": "9876543210987654",
                "card_cvv": "123"
            }
        ]
    }
}

# Mock OTP storage (in a real system, this would be in a secure database)
pending_otps = {}
auth_otps = {}  # Store authentication OTPs
payment_otps = {}  # Store payment OTPs

app = Flask(__name__)

# Mock data - expanded dates and time slots (convert to DD-MM-YYYY format)
available_slots = {
    "05-04-2025": ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00"],
    "06-04-2025": ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00"],
    "07-04-2025": ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00"],
    "08-04-2025": ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00"],
    "09-04-2025": ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00"],
    "10-04-2025": ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00"],
    "11-04-2025": ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30", "17:00"],
    "12-04-2025": ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00"],
    "13-04-2025": ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00"],
}

# General doctors
doctors = [
    {"id": "doc1", "name": "Dr. Mark Evans", "specialization": "General Medicine", "price": 75},
    {"id": "doc2", "name": "Dr. Sarah Johnson", "specialization": "Family Medicine", "price": 85},
    {"id": "doc3", "name": "Dr. James Wilson", "specialization": "Internal Medicine", "price": 95},
    {"id": "doc4", "name": "Dr. Anna White", "specialization": "General Medicine", "price": 70},
    {"id": "doc5", "name": "Dr. Thomas Brown", "specialization": "Family Medicine", "price": 80},
    {"id": "doc6", "name": "Dr. Emily Carter", "specialization": "Internal Medicine", "price": 90},
    {"id": "doc7", "name": "Dr. William Davis", "specialization": "General Medicine", "price": 75},
    {"id": "doc8", "name": "Dr. Olivia Martinez", "specialization": "Family Medicine", "price": 85},
    {"id": "doc9", "name": "Dr. Benjamin Taylor", "specialization": "Internal Medicine", "price": 95},
    {"id": "doc10", "name": "Dr. Sophia Anderson", "specialization": "General Medicine", "price": 70},
    {"id": "doc61", "name": "Dr. Robert Johnson", "specialization": "General Medicine", "price": 75},
    {"id": "doc62", "name": "Dr. Emma Williams", "specialization": "Family Medicine", "price": 85},
    {"id": "doc63", "name": "Dr. Michael Davis", "specialization": "Internal Medicine", "price": 95},
    {"id": "doc64", "name": "Dr. Olivia Clark", "specialization": "General Medicine", "price": 70},
    {"id": "doc65", "name": "Dr. David Martinez", "specialization": "Family Medicine", "price": 80},
    {"id": "doc66", "name": "Dr. Sophia Rodriguez", "specialization": "Internal Medicine", "price": 90},
    {"id": "doc67", "name": "Dr. John Lee", "specialization": "General Medicine", "price": 75},
    {"id": "doc68", "name": "Dr. Isabella Garcia", "specialization": "Family Medicine", "price": 85},
    {"id": "doc69", "name": "Dr. William Brown", "specialization": "Internal Medicine", "price": 95},
    {"id": "doc70", "name": "Dr. Ava Lopez", "specialization": "General Medicine", "price": 70},
    {"id": "doc71", "name": "Dr. James Singh", "specialization": "Family Medicine", "price": 80},
    {"id": "doc72", "name": "Dr. Charlotte Patel", "specialization": "Internal Medicine", "price": 90},
    {"id": "doc73", "name": "Dr. Benjamin Kim", "specialization": "General Medicine", "price": 75},
    {"id": "doc74", "name": "Dr. Mia Nguyen", "specialization": "Family Medicine", "price": 85},
    {"id": "doc75", "name": "Dr. Daniel Chen", "specialization": "Internal Medicine", "price": 95},
    {"id": "doc76", "name": "Dr. Elizabeth Wong", "specialization": "General Medicine", "price": 70},
    {"id": "doc77", "name": "Dr. Matthew Smith", "specialization": "Family Medicine", "price": 80},
    {"id": "doc78", "name": "Dr. Abigail Wilson", "specialization": "Internal Medicine", "price": 90},
    {"id": "doc79", "name": "Dr. Ethan Taylor", "specialization": "General Medicine", "price": 75},
    {"id": "doc80", "name": "Dr. Sofia Hernandez", "specialization": "Family Medicine", "price": 85},
]

# Add specialized doctors with expanded specializations and fixed prices
specialized_doctors = [
    {"id": "doc11", "name": "Dr. Emily Chen", "specialization": "Cardiology", "price": 225},
    {"id": "doc12", "name": "Dr. Robert Miller", "specialization": "Dermatology", "price": 185},
    {"id": "doc13", "name": "Dr. Lisa Wong", "specialization": "Neurology", "price": 260},
    {"id": "doc14", "name": "Dr. Michael Brown", "specialization": "Dermatology", "price": 195},
    {"id": "doc15", "name": "Dr. Jennifer Davis", "specialization": "Orthopedics", "price": 210},
    {"id": "doc16", "name": "Dr. David Lee", "specialization": "Ophthalmology", "price": 200},
    {"id": "doc17", "name": "Dr. Amanda Patel", "specialization": "Gastroenterology", "price": 230},
    {"id": "doc18", "name": "Dr. Richard Wilson", "specialization": "Endocrinology", "price": 220},
    {"id": "doc19", "name": "Dr. Jessica Martinez", "specialization": "Rheumatology", "price": 215},
    {"id": "doc20", "name": "Dr. Kevin Thompson", "specialization": "Urology", "price": 195},
    {"id": "doc21", "name": "Dr. Stephanie Garcia", "specialization": "Pulmonology", "price": 225},
    {"id": "doc22", "name": "Dr. Andrew Clark", "specialization": "Nephrology", "price": 235},
    {"id": "doc23", "name": "Dr. Nicole Wright", "specialization": "Hematology", "price": 245},
    {"id": "doc24", "name": "Dr. Jonathan Scott", "specialization": "Oncology", "price": 300},
    {"id": "doc25", "name": "Dr. Rachel Kim", "specialization": "Immunology", "price": 240},
    {"id": "doc26", "name": "Dr. Brian Adams", "specialization": "Psychiatry", "price": 210},
    {"id": "doc27", "name": "Dr. Michelle Lewis", "specialization": "Allergy", "price": 180},
    {"id": "doc28", "name": "Dr. Daniel Murphy", "specialization": "Physical Therapy", "price": 150},
    {"id": "doc29", "name": "Dr. Lauren Baker", "specialization": "Pediatric Cardiology", "price": 250},
    {"id": "doc30", "name": "Dr. Christopher Hall", "specialization": "Obstetrics", "price": 210},
    {"id": "doc31", "name": "Dr. Amanda Rodriguez", "specialization": "Gynecology", "price": 195},
    {"id": "doc32", "name": "Dr. Matthew Turner", "specialization": "Sports Medicine", "price": 180},
    {"id": "doc33", "name": "Dr. Elizabeth Nelson", "specialization": "Geriatrics", "price": 165},
    {"id": "doc34", "name": "Dr. Joseph Collins", "specialization": "Otolaryngology", "price": 220},
    {"id": "doc35", "name": "Dr. Rebecca Hill", "specialization": "Plastic Surgery", "price": 350},
    {"id": "doc36", "name": "Dr. Steven Green", "specialization": "Vascular Surgery", "price": 400},
    {"id": "doc37", "name": "Dr. Kimberly Ross", "specialization": "Neurosurgery", "price": 500},
    {"id": "doc38", "name": "Dr. Eric Cooper", "specialization": "Cardiothoracic Surgery", "price": 575},
    {"id": "doc39", "name": "Dr. Laura Morgan", "specialization": "Pediatrics", "price": 140},
    {"id": "doc40", "name": "Dr. Timothy Bennett", "specialization": "Neonatology", "price": 250},
    {"id": "doc41", "name": "Dr. Christine Stewart", "specialization": "Infectious Disease", "price": 210},
    {"id": "doc42", "name": "Dr. Ryan Phillips", "specialization": "Emergency Medicine", "price": 210},
    {"id": "doc43", "name": "Dr. Julia Reed", "specialization": "Anesthesiology", "price": 290},
    {"id": "doc44", "name": "Dr. Gregory Patterson", "specialization": "Radiology", "price": 240},
    {"id": "doc45", "name": "Dr. Heather Foster", "specialization": "Nuclear Medicine", "price": 260},
    {"id": "doc46", "name": "Dr. Brandon Hughes", "specialization": "Pathology", "price": 225},
    {"id": "doc47", "name": "Dr. Vanessa Rivera", "specialization": "Occupational Medicine", "price": 170},
    {"id": "doc48", "name": "Dr. Nathan Russell", "specialization": "Pain Management", "price": 195},
    {"id": "doc49", "name": "Dr. Alice Powell", "specialization": "Sleep Medicine", "price": 180},
    {"id": "doc50", "name": "Dr. Adam Peterson", "specialization": "Addiction Medicine", "price": 210},
    {"id": "doc51", "name": "Dr. Catherine Sanders", "specialization": "Rehabilitation", "price": 150},
    {"id": "doc52", "name": "Dr. Derek Watson", "specialization": "Palliative Care", "price": 180},
    {"id": "doc53", "name": "Dr. Megan Barnes", "specialization": "Preventive Medicine", "price": 140},
    {"id": "doc54", "name": "Dr. Tyler Griffin", "specialization": "Nutrition", "price": 120},
    {"id": "doc55", "name": "Dr. Victoria Hayes", "specialization": "Podiatry", "price": 150},
    {"id": "doc56", "name": "Dr. Spencer Coleman", "specialization": "Chiropractic", "price": 110},
    {"id": "doc57", "name": "Dr. Natalie Bell", "specialization": "Acupuncture", "price": 120},
    {"id": "doc58", "name": "Dr. Dylan Brooks", "specialization": "Holistic Medicine", "price": 135},
    {"id": "doc59", "name": "Dr. Hannah Wood", "specialization": "Genetics", "price": 265},
    {"id": "doc60", "name": "Dr. Jason King", "specialization": "Clinical Psychology", "price": 185},
]

# Clinics data with more detailed services and fixed prices
clinics = {
    "City Health Clinic": {
        "rating": 4.7,
        "address": "123 Main St, Downtown",
        "hours": "Mon-Fri: 8am-6pm, Sat: 9am-1pm",
        "services": [
            "General check-ups", 
            "Vaccinations", 
            "Basic blood work", 
            "Flu treatments", 
            "Allergy testing", 
            "Minor injury care", 
            "Health screenings"
        ],
        "price_list": {
            "General Medicine": 75,
            "Vaccinations": 50,
            "Blood Work": 90,
            "Health Screenings": 80
        },
        "waiting_time": "15-20 minutes",
        "specializations": ["General Medicine", "Family Medicine"],
        "requires_payment": True
    },
    "Downtown Family Care": {
        "rating": 4.5,
        "address": "456 Oak Ave, Midtown",
        "hours": "Mon-Fri: 9am-7pm, Sat-Sun: 10am-2pm",
        "services": [
            "Family care", 
            "Pediatrics", 
            "Senior care", 
            "Women's health", 
            "Chronic disease management",
            "Mental health screenings",
            "Nutritional counseling"
        ],
        "price_list": {
            "General Medicine": 0,
            "Pediatrics": 100,
            "Senior Care": 115,
            "Women's Health": 110
        },
        "waiting_time": "20-30 minutes",
        "specializations": ["Family Medicine", "Internal Medicine"],
        "requires_payment": False,
        "free_services": ["General Medicine"]
    },
    "Good Health Clinic": {
        "rating": 4.8,
        "address": "789 Pine St, Westside",
        "hours": "Mon-Fri: 8am-8pm, Sat: 9am-3pm",
        "services": [
            "Dermatology", 
            "Skin treatments", 
            "Cosmetic procedures", 
            "Acne management", 
            "Skin cancer screenings", 
            "Eczema treatment", 
            "Laser therapy"
        ],
        "price_list": {
            "Dermatology Consultation": 185,
            "Skin Treatments": 250,
            "Cosmetic Procedures": 600,
            "Laser Therapy": 325
        },
        "waiting_time": "10-15 minutes",
        "specializations": ["Dermatology", "Cosmetic Dermatology"],
        "requires_payment": True
    },
    "My Skin Care": {
        "rating": 4.6,
        "address": "321 Maple Rd, Eastside",
        "hours": "Mon-Sat: 8am-7pm",
        "services": [
            "Dermatology", 
            "Skin biopsies", 
            "Allergies", 
            "In-house diagnostics", 
            "Psoriasis treatment", 
            "Fungal infection treatment", 
            "Skin rejuvenation"
        ],
        "price_list": {
            "Dermatology": 195,
            "Allergy Testing": 200,
            "Skin Biopsies": 300,
            "Diagnostic Services": 250
        },
        "waiting_time": "20 minutes during peak hours",
        "specializations": ["Dermatology", "Allergology"],
        "requires_payment": True
    },
    "My Health Clinic": {
        "rating": 4.5,
        "address": "555 Health Blvd, Northside",
        "hours": "Mon-Fri: 7am-7pm, Sat: 8am-2pm",
        "services": [
            "General check-ups", 
            "Preventive care", 
            "Blood tests", 
            "Immunizations", 
            "Health screenings", 
            "Wellness exams", 
            "Minor illness treatment"
        ],
        "price_list": {
            "General Medicine": 85,
            "Preventive Care": 75,
            "Blood Tests": 95,
            "Immunizations": 60
        },
        "waiting_time": "15-25 minutes",
        "specializations": ["General Medicine", "Preventive Medicine"],
        "requires_payment": True
    },
    "Heart & Vascular Center": {
        "rating": 4.9,
        "address": "555 Cardio Lane, Northside",
        "hours": "Mon-Fri: 7am-6pm",
        "services": [
            "Cardiac evaluations",
            "ECG/EKG testing",
            "Stress tests",
            "Heart disease management",
            "Blood pressure monitoring",
            "Cholesterol management",
            "Cardiac rehabilitation"
        ],
        "price_list": {
            "cardiology": 250,
            "Cardiac Testing": 350,
            "Cardiology Consultation": 225,
            "Heart Disease Management": 275,
            "Rehabilitation Services": 175
        },
        "waiting_time": "15-25 minutes",
        "specializations": ["Cardiology", "Vascular Medicine"],
        "requires_payment": True
    },
    "Neurology Associates": {
        "rating": 4.8,
        "address": "789 Brain Way, Medical District",
        "hours": "Mon-Fri: 8am-5pm",
        "services": [
            "Neurological evaluations",
            "Headache treatment",
            "Seizure management",
            "Memory disorder assessment",
            "Nerve condition testing",
            "Movement disorder treatment",
            "Sleep disorder evaluation"
        ],
        "price_list": {
            "Neurology Consultation": 260,
            "Cognitive Testing": 300,
            "EEG Studies": 375,
            "Sleep Studies": 500
        },
        "waiting_time": "20-30 minutes",
        "specializations": ["Neurology", "Sleep Medicine"]
    },
    "Orthopedic Specialists": {
        "rating": 4.7,
        "address": "456 Joint Street, Sports District",
        "hours": "Mon-Fri: 7am-7pm, Sat: 8am-12pm",
        "services": [
            "Joint pain management",
            "Sports injury treatment",
            "Fracture care",
            "Arthritis management",
            "Physical therapy",
            "Orthopedic surgery consultation",
            "Rehabilitation services"
        ],
        "price_list": {
            "Orthopedic Consultation": 210,
            "Sports Medicine": 180,
            "Physical Therapy": 115,
            "Joint Injections": 225
        },
        "waiting_time": "15-25 minutes",
        "specializations": ["Orthopedics", "Sports Medicine"]
    },
    "Women's Health Center": {
        "rating": 4.9,
        "address": "123 Care Boulevard, Eastside",
        "hours": "Mon-Fri: 8am-6pm, Sat: 9am-1pm",
        "services": [
            "OB/GYN services",
            "Prenatal care",
            "Fertility counseling",
            "Menopause management",
            "Women's wellness exams",
            "Mammography",
            "Gynecological procedures"
        ],
        "price_list": {
            "OB/GYN Consultation": 195,
            "Prenatal Care": 250,
            "Gynecological Procedures": 400,
            "Wellness Exams": 150
        },
        "waiting_time": "15-20 minutes",
        "specializations": ["Obstetrics", "Gynecology"]
    },
    "Pediatric Care Center": {
        "rating": 4.8,
        "address": "789 Child Lane, Family District",
        "hours": "Mon-Fri: 8am-7pm, Sat: 9am-3pm",
        "services": [
            "Well-child visits",
            "Immunizations",
            "Growth monitoring",
            "Developmental assessments",
            "Pediatric illness treatment",
            "School/sports physicals",
            "Newborn care"
        ],
        "price_list": {
            "Pediatric Consultation": 140,
            "Immunizations": 65,
            "Physical Exams": 90,
            "Newborn Care": 150
        },
        "waiting_time": "15-30 minutes",
        "specializations": ["Pediatrics", "Adolescent Medicine"]
    },
    "Mental Health Clinic": {
        "rating": 4.6,
        "address": "456 Wellness Road, Riverside",
        "hours": "Mon-Fri: 9am-7pm, Sat: 10am-4pm",
        "services": [
            "Psychiatric evaluations",
            "Therapy sessions",
            "Depression treatment",
            "Anxiety management",
            "Medication management",
            "Group therapy",
            "Stress management"
        ],
        "price_list": {
            "Psychiatric Consultation": 210,
            "Therapy Sessions": 150,
            "Medication Management": 180,
            "Group Therapy": 90
        },
        "waiting_time": "15-20 minutes",
        "specializations": ["Psychiatry", "Clinical Psychology"]
    },
    "Dental Care Center": {
        "rating": 4.7,
        "address": "789 Tooth Avenue, Westside",
        "hours": "Mon-Fri: 8am-6pm, Sat: 9am-2pm",
        "services": [
            "Dental check-ups",
            "Cleanings",
            "Fillings",
            "Root canals",
            "Crowns and bridges",
            "Teeth whitening",
            "Oral surgery"
        ],
        "price_list": {
            "Dental Consultation": 90,
            "Cleaning": 120,
            "Filling": 180,
            "Root Canal": 700
        },
        "waiting_time": "10-20 minutes",
        "specializations": ["General Dentistry", "Cosmetic Dentistry"]
    },
    "Vision Care Specialists": {
        "rating": 4.8,
        "address": "456 Eye Street, Northside",
        "hours": "Mon-Fri: 9am-7pm, Sat: 10am-4pm",
        "services": [
            "Eye exams",
            "Vision testing",
            "Contact lens fittings",
            "Glaucoma screenings",
            "Cataract evaluations",
            "Diabetic eye care",
            "LASIK consultations"
        ],
        "price_list": {
            "Eye Examination": 120,
            "Contact Lens Fitting": 85,
            "Glaucoma Screening": 95,
            "Cataract Evaluation": 150
        },
        "waiting_time": "15-25 minutes",
        "specializations": ["Optometry", "Ophthalmology"]
    },
    "Sports Medicine Center": {
        "rating": 4.9,
        "address": "123 Athletic Drive, Sports District",
        "hours": "Mon-Fri: 7am-8pm, Sat: 8am-3pm",
        "services": [
            "Sports injury treatment",
            "Performance evaluation",
            "Athletic training",
            "Rehabilitation",
            "Nutrition counseling",
            "Concussion management",
            "Sports physicals"
        ],
        "price_list": {
            "Sports Medicine Consultation": 180,
            "Performance Evaluation": 220,
            "Rehabilitation Session": 115,
            "Sports Physical": 100
        },
        "waiting_time": "10-20 minutes",
        "specializations": ["Sports Medicine", "Physical Therapy"]
    },
    "Allergy & Asthma Center": {
        "rating": 4.7,
        "address": "789 Breeze Lane, Eastside",
        "hours": "Mon-Fri: 8am-5pm",
        "services": [
            "Allergy testing",
            "Immunotherapy",
            "Asthma management",
            "Respiratory evaluations",
            "Food allergy testing",
            "Eczema treatment",
            "Sinus disorder management"
        ],
        "price_list": {
            "Allergy Consultation": 180,
            "Allergy Testing": 250,
            "Immunotherapy": 190,
            "Asthma Management": 170
        },
        "waiting_time": "15-25 minutes",
        "specializations": ["Allergy", "Immunology"]
    },
    # Additional clinics by state and specialization
    
    # California Clinics
    "Hyderabad Heart Institute": {
        "rating": 4.9,
        "address": "123 Cardiac Way, Hyderabad, India",
        "hours": "Mon-Fri: 7am-6pm",
        "services": [
            "Cardiac evaluations",
            "ECG/EKG testing",
            "Stress tests",
            "Heart disease management",
            "Cardiac rehabilitation"
        ],
        "price_list": {
            "cardiology": 0,
            "Cardiac Testing": 0,
            "Cardiology Consultation": 0,
            "Heart Disease Management": 0
        },
        "waiting_time": "15-20 minutes",
        "specializations": ["Cardiology", "Vascular Medicine"],
        "requires_payment": False,
        "free_services": ["Cardiology", "Cardiac Testing", "Cardiology Consultation", "Heart Disease Management"]
    },
    # Rest of clinics data
    
}

# Add a new function to deterministically select doctors by specialization
def get_doctor_for_specialization(specialization):
    """
    Deterministically select a doctor for a given specialization.
    This ensures the same doctor is always returned for the same specialization.
    """
    if not specialization:
        # If no specialization, use the first general doctor
        return doctors[0]
    
    # Convert to lowercase for case-insensitive matching
    specialization = specialization.lower()
    
    # Check if this is a general health consultation
    general_health_terms = ["general health", "general medicine", "family medicine", "general", "check-up", "checkup", "check up", "primary care"]
    
    if any(term in specialization for term in general_health_terms):
        # For general health, prioritize general practitioners
        general_doctors = [doc for doc in doctors if doc["specialization"].lower() in ["general medicine", "family medicine"]]
        if general_doctors:
            return general_doctors[0]
        # If no specific general doctors found, return the first doctor
        return doctors[0]
    
    # For specialized care, look in specialized doctors first
    matching_doctors = [doc for doc in specialized_doctors if doc["specialization"].lower() == specialization]
    
    # If no exact match, try partial match on specialized doctors
    if not matching_doctors:
        matching_doctors = [doc for doc in specialized_doctors if specialization in doc["specialization"].lower()]
    
    # If still no match, look for partial matches in general doctors
    if not matching_doctors:
        matching_doctors = [doc for doc in doctors if specialization in doc["specialization"].lower()]
    
    # If no matching doctors found at all, use first general doctor
    if not matching_doctors:
        matching_doctors = doctors
    
    # Use the first matching doctor for consistency
    # This ensures the same doctor is always returned for a given specialization
    return matching_doctors[0]

@app.route('/')
def index():
    """Simple health check endpoint"""
    return jsonify({"status": "Server is running"})

@app.route('/check_clinics_availability', methods=['GET'])
def check_clinics_availability():
    """Check if a specific date and time slot is available"""
    date_str = request.args.get('date', '05-04-2025')  # Default now in DD-MM-YYYY
    time_str = request.args.get('time', '10:00 AM')
    specialization = request.args.get('specialization', '')
    clinic_name = request.args.get('clinic', '')
    
    logger.info(f"Checking availability for date: {date_str}, time: {time_str}, specialization: {specialization}, clinic: {clinic_name}")
    
    # Get a consistent doctor for this specialization
    selected_doctor = get_doctor_for_specialization(specialization)
    
    # Mark 12:30 PM slot as unavailable
    is_available = True
    if time_str.lower() == "12:30 pm":
        is_available = False
    
    response = {
        "is_available": is_available,
        "date": date_str,
        "time": time_str,
        "formatted_datetime": f"{date_str} at {time_str}",
        "doctor": selected_doctor
    }
    
    # Add clinic information if provided
    if clinic_name and clinic_name in clinics:
        response["clinic"] = {
            "name": clinic_name,
            "details": clinics[clinic_name]
        }
    
    logger.info(f"Returning response: {response}")
    return jsonify(response)

@app.route('/get_clinics', methods=['GET'])
def get_clinics():
    """Get clinics based on type, location, and filtered by best rating"""
    clinic_type = request.args.get('type', '')  # Specialization type
    
    logger.info(f"Getting clinics with type: {clinic_type}")
    
    # Initialize result clinics
    result_clinics = []
    
    # If cardiology type is requested, return the cardiology clinics
    if clinic_type.lower() == 'cardiology':
        # Add Heart & Vascular Center
        if "Heart & Vascular Center" in clinics:
            result_clinics.append({"name": "Heart & Vascular Center", **clinics["Heart & Vascular Center"]})
        
        # Add Hyderabad Heart Institute
        if "Hyderabad Heart Institute" in clinics:
            result_clinics.append({"name": "Hyderabad Heart Institute", **clinics["Hyderabad Heart Institute"]})
    # If dermatology type is requested, return the dermatology clinics
    elif clinic_type.lower() == 'dermatology':
        # Add Good Health Clinic
        if "Good Health Clinic" in clinics:
            result_clinics.append({"name": "Good Health Clinic", **clinics["Good Health Clinic"]})
        
        # Add My Skin Care
        if "My Skin Care" in clinics:
            result_clinics.append({"name": "My Skin Care", **clinics["My Skin Care"]})
    else:
        # For all other types, return the default clinics
        # Add City Health Clinic
        if "City Health Clinic" in clinics:
            result_clinics.append({"name": "City Health Clinic", **clinics["City Health Clinic"]})
        
        # Add Downtown Family Care
        if "Downtown Family Care" in clinics:
            result_clinics.append({"name": "Downtown Family Care", **clinics["Downtown Family Care"]})
            
        # Add My Health Clinic
        if "My Health Clinic" in clinics:
            result_clinics.append({"name": "My Health Clinic", **clinics["My Health Clinic"]})
    
    logger.info(f"Returning {len(result_clinics)} clinics")
    return jsonify({
        "status": "success",
        "clinics": result_clinics
    })

@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    """Book an appointment"""
    data = request.json or {}
    specialization = data.get('specialization', '')
    appointment_time = data.get('time', '')
    
    logger.info(f"Booking appointment with data: {data}")
    
    # Check if appointment time is 12:00 PM
    if appointment_time == "12:00 PM" or appointment_time == "12 PM":
        response = {
            "status": "error",
            "confirmed": False,
            "message": "appointment time is not available",
            "details": data
        }
        logger.info(f"Appointment response: {response}")
        return jsonify(response), 409
    
    # Always return success for demo
    appointment_id = "APPT" + str(random.randint(1000, 9999))
    
    response = {
        "status": "success",
        "confirmed": True,
        "appointment_id": appointment_id,
        "message": "Appointment successfully booked",
        "details": data
    }
    
    # Use the same doctor selection logic as check_availability
    if specialization:
        response["doctor"] = get_doctor_for_specialization(specialization)
            
    logger.info(f"Appointment response: {response}")
    return jsonify(response)

@app.route('/add_payment_method', methods=['POST'])
def add_payment_method():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    # Get required fields from the request
    phone_number = data.get('phone_number')
    card_number = data.get('card_number')
    card_expiry_month = data.get('card_expiry_month')
    card_expiry_year = data.get('card_expiry_year')
    card_type = data.get('card_type', 'credit')  # Default to credit if not specified
    card_brand = data.get('card_brand', 'visa')  # Default to visa if not specified

    # Validate required fields
    if not all([phone_number, card_number, card_expiry_month, card_expiry_year]):
        missing_fields = []
        if not phone_number:
            missing_fields.append('phone_number')
        if not card_number:
            missing_fields.append('card_number')
        if not card_expiry_month:
            missing_fields.append('card_expiry_month')
        if not card_expiry_year:
            missing_fields.append('card_expiry_year')
            
        return jsonify({
            "status": "error", 
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400

    # Find the user by phone number

    # Validate card information (basic validation)
    if len(card_number) < 13 or len(card_number) > 19:
        return jsonify({"status": "error", "message": "Invalid card number length"}), 400
    
    try:
        expiry_month = int(card_expiry_month)
        expiry_year = int(card_expiry_year)
        if expiry_month < 1 or expiry_month > 12:
            return jsonify({"status": "error", "message": "Invalid expiry month"}), 400
        
        current_year = datetime.now().year % 100  # Get last two digits of year
        if expiry_year < current_year:
            return jsonify({"status": "error", "message": "Card has expired"}), 400
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid expiry date format"}), 400

    
    return jsonify({
        "status": "success", 
        "message": "Payment method added successfully",
        "payment_method": {
            "card_last_4": card_number[-4:],
            "card_type": card_type,
            "card_brand": card_brand
        }
    })

@app.route('/initiate_payment', methods=['POST'])
def initiate_payment():
    """Initiate payment through payment gateway and get OTP request."""
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    # Get required fields from the request
    phone_number = data.get('phone_number')
    clinic_name = data.get('clinic_name')
    amount = data.get('amount')
    currency = data.get('currency', 'USD')  # Default to USD if not provided
    
    # Card information
    card_number = data.get('card_number')
    card_expiry_month = data.get('card_expiry_month')
    card_expiry_year = data.get('card_expiry_year')
    card_cvv = data.get('card_cvv')
    card_holder_name = data.get('card_holder_name')

    # Validate required fields
    if not all([phone_number, clinic_name, amount, card_number, card_expiry_month, card_expiry_year, card_cvv, card_holder_name]):
        missing_fields = []
        if not phone_number:
            missing_fields.append('phone_number')
        if not clinic_name:
            missing_fields.append('clinic_name')
        if not amount:
            missing_fields.append('amount')
        if not card_number:
            missing_fields.append('card_number')
        if not card_expiry_month:
            missing_fields.append('card_expiry_month')
        if not card_expiry_year:
            missing_fields.append('card_expiry_year')
        if not card_cvv:
            missing_fields.append('card_cvv')
        if not card_holder_name:
            missing_fields.append('card_holder_name')
            
        return jsonify({
            "status": "error", 
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400

    # Validate amount is a positive number
    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({"status": "error", "message": "Amount must be greater than 0"}), 400
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid amount format"}), 400

    # Validate card information
    if len(card_number) < 13 or len(card_number) > 19:
        return jsonify({"status": "error", "message": "Invalid card number length"}), 400
    
    try:
        expiry_month = int(card_expiry_month)
        expiry_year = int(card_expiry_year)
        if expiry_month < 1 or expiry_month > 12:
            return jsonify({"status": "error", "message": "Invalid expiry month"}), 400
        
        current_year = datetime.now().year % 100  # Get last two digits of year
        if expiry_year < current_year:
            return jsonify({"status": "error", "message": "Card has expired"}), 400
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid expiry date format"}), 400

    # Validate CVV
    if not (len(card_cvv) in [3, 4] and card_cvv.isdigit()):
        return jsonify({"status": "error", "message": "Invalid CVV"}), 400

    # Find the user by phone number
    user = registered_users.get(phone_number)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    # Validate clinic exists
    if clinic_name not in clinics:
        return jsonify({"status": "error", "message": "Clinic not found"}), 404

    # Generate transaction ID
    transaction_id = f"TR-{uuid.uuid4().hex[:10].upper()}"
    timestamp = datetime.now().isoformat()

    # Mock payment gateway response
    payment_gateway_response = {
        "status": "pending",
        "message": "OTP sent to registered mobile number",
        "transaction_id": transaction_id,
        "gateway_reference": f"PG-{uuid.uuid4().hex[:8].upper()}",
        "requires_otp": True
    }

    # Record the payment initiation
    payment = {
        "transaction_id": transaction_id,
        "gateway_reference": payment_gateway_response["gateway_reference"],
        "amount": amount,
        "currency": currency,
        "clinic_name": clinic_name,
        "card_last_4": card_number[-4:],
        "card_holder_name": card_holder_name,
        "status": "pending",
        "timestamp": timestamp
    }

    # Add payment to user's transaction history
    if "payments" not in user:
        user["payments"] = []
    user["payments"].append(payment)

    # Log the payment initiation
    logger.info(f"Payment initiated: {transaction_id} for {clinic_name}")

    return jsonify({
        "status": "success",
        "message": "Payment initiated successfully. Please verify OTP to complete the payment.",
        "transaction_id": transaction_id,
        "gateway_reference": payment_gateway_response["gateway_reference"],
        "amount": amount,
        "currency": currency,
        "requires_otp": True
    })

@app.route('/verify_payment_otp', methods=['POST'])
def verify_payment_otp():
    """Verify OTP with payment gateway to complete the payment."""
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400

    # Get required fields from the request
    phone_number = data.get('phone_number')
    otp = data.get('otp')
    transaction_id = data.get('transaction_id')
    print("phone_number, otp, transaction_id", phone_number, otp, transaction_id)
    # Validate required fields
    if not all([phone_number, otp, transaction_id]):
        missing_fields = []
        if not phone_number:
            missing_fields.append('phone_number')
        if not otp:
            missing_fields.append('otp')
        if not transaction_id:
            missing_fields.append('transaction_id')
            
        return jsonify({
            "status": "error", 
            "message": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400

    # Find the user by phone number
    user = registered_users.get(phone_number)
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    # Find the payment record
    payment = None
    for p in user.get('payments', []):
        if p.get('transaction_id') == transaction_id:
            payment = p
            break

    if not payment:
        return jsonify({"status": "error", "message": "Transaction not found"}), 404

    # Mock payment gateway OTP verification
    if otp == "987654":
        # Update payment status
        payment['status'] = 'completed'
        payment['verified_at'] = datetime.now().isoformat()
        
        # Mock successful payment gateway response
        gateway_response = {
            "status": "success",
            "message": "Payment completed successfully",
            "gateway_reference": payment.get('gateway_reference'),
            "transaction_id": transaction_id,
            "amount": payment.get('amount'),
            "currency": payment.get('currency'),
            "completed_at": datetime.now().isoformat(),
            "card_details": {
                "last4": payment.get('card_last_4'),
                "type": "credit",  # Default to credit card
                "brand": "visa"    # Default to visa
            }
        }

        logger.info(f"Payment completed successfully for transaction: {transaction_id}")
        
        return jsonify(gateway_response)
    else:
        # Mock failed payment gateway response
        logger.warning(f"Invalid OTP attempt for transaction: {transaction_id}")
        return jsonify({
            "status": "error",
            "message": "Invalid OTP",
            "transaction_id": transaction_id,
            "gateway_reference": payment.get('gateway_reference'),
            "card_details": {
                "last4": payment.get('card_last_4'),
                "type": "credit",
                "brand": "visa"
            }
        }), 400

@app.route('/create_account', methods=['POST'])
def create_account():
    """Create a new user account and send OTP."""
    data = request.json or {}
    phone_number = data.get('phone_number')
    user_name = data.get('user_name')
    
    if not phone_number or not user_name:
        return jsonify({
            "status": "error",
            "message": "Phone number and user name are required"
        }), 400
    
    # Check if user already exists
    if phone_number in registered_users:
        return jsonify({
            "status": "error",
            "message": "Account already exists with this phone number"
        }), 409
    
    # Generate OTP (in real system, this would be sent via SMS)
    otp = str(random.randint(100000, 999999))
    pending_otps[phone_number] = {
        "otp": otp,
        "user_name": user_name,
        "expires_at": time.time() + 300  # 5 minutes expiry
    }
    
    logger.info(f"Generated OTP {otp} for phone number {phone_number}")
    
    return jsonify({
        "status": "success",
        "message": "Account creation initiated. Please verify OTP.",
        "otp": otp  # In production, this would be sent via SMS instead
    })

@app.route('/verify_account_creation_otp', methods=['POST'])
def verify_account_creation_otp():
    """Verify OTP and create account."""
    data = request.json or {}
    phone_number = data.get('phone_number')
    otp = data.get('otp')
    
    # For testing purposes, always succeed
    if phone_number not in registered_users:
        registered_users[phone_number] = {
            "user_name": "Test User",  # Default name if not found in pending_otps
            "payment_methods": []
        }
        
        # If we have pending data, use it
        if phone_number in pending_otps:
            registered_users[phone_number]["user_name"] = pending_otps[phone_number]['user_name']
            del pending_otps[phone_number]
    
    return jsonify({
        "status": "success",
        "message": "Account created successfully",
        "user": {
            "phone_number": phone_number,
            "user_name": registered_users[phone_number]["user_name"]
        }
    })

@app.route('/check_payment_required', methods=['GET'])
def check_payment_required():
    """Check if a clinic requires payment for appointments."""
    clinic_name = request.args.get('clinic_name')
    
    if not clinic_name:
        return jsonify({
            "status": "error",
            "message": "Clinic name is required"
        }), 400
    
    clinic_data = clinics.get(clinic_name)
    if not clinic_data:
        return jsonify({
            "status": "error",
            "message": "Clinic not found"
        }), 404
    
    requires_payment = clinic_data.get("requires_payment", False)
    
    return jsonify({
        "status": "success",
        "clinic_name": clinic_name,
        "requires_payment": requires_payment
    })

@app.route('/get_nearest_available_slots', methods=['GET'])
def get_nearest_available_slots():
    """Find nearest available time slots when a specific slot is unavailable"""
    date_str = request.args.get('date', '05-04-2025')  # Default now in DD-MM-YYYY
    time_str = request.args.get('time', '12:30 PM')  # Usually this will be the unavailable slot
    clinic_name = request.args.get('clinic', '')
    
    logger.info(f"Finding nearest available slots for date: {date_str}, time: {time_str}, clinic: {clinic_name}")
    
    # Generate 3 nearest available time slots
    # In a real implementation, this would query a database of available slots
    # For demo purposes, we'll generate time slots around the requested time
    
    # Convert request time to datetime for easier manipulation
    import datetime
    from datetime import timedelta
    import re
    
    # Parse the time string (assuming format like "12:30 PM")
    time_match = re.match(r'(\d+):(\d+)\s+(AM|PM)', time_str)
    if time_match:
        hour, minute, ampm = time_match.groups()
        hour = int(hour)
        minute = int(minute)
        
        # Adjust hour for PM
        if ampm == 'PM' and hour < 12:
            hour += 12
        elif ampm == 'AM' and hour == 12:
            hour = 0
            
        # Parse the DD-MM-YYYY date
        day, month, year = date_str.split('-')
        base_date = datetime.datetime(int(year), int(month), int(day))
            
        base_time = datetime.datetime.combine(
            base_date.date(),
            datetime.time(hour, minute)
        )
        
        # Generate time slots at 30-minute intervals (before and after the requested time)
        available_slots = []
        offsets = [-60, -30, 30, 60, 90]  # minutes to offset (negative = earlier, positive = later)
        
        for offset in offsets:
            slot_time = base_time + timedelta(minutes=offset)
            
            # Only add slots during business hours (8 AM to 6 PM)
            if 8 <= slot_time.hour < 18:
                # Format the time for display
                hour_12 = slot_time.hour % 12
                if hour_12 == 0:
                    hour_12 = 12
                ampm = 'AM' if slot_time.hour < 12 else 'PM'
                formatted_time = f"{hour_12}:{slot_time.minute:02d} {ampm}"
                
                # Skip the original requested time (which would be unavailable)
                if formatted_time != time_str:
                    # Format date as DD-MM-YYYY
                    slot_date = slot_time.strftime('%d-%m-%Y')
                    available_slots.append({
                        "date": slot_date,
                        "time": formatted_time,
                        "formatted_datetime": f"{slot_date} at {formatted_time}"
                    })
        
        # Add a slot for the next day, but avoid using 12:30 PM which is known to be unavailable
        next_day_date = (base_time + timedelta(days=1)).date()
        next_day_date_str = next_day_date.strftime('%d-%m-%Y')
        
        # Check if the original time is 12:30 PM (which we know is unavailable)
        if time_str == "12:30 PM":
            # Use 1:00 PM instead for the next day
            next_day_time = "1:00 PM"
        else:
            next_day_time = time_str
            
        next_day_slot = {
            "date": next_day_date_str,
            "time": next_day_time,
            "formatted_datetime": f"{next_day_date_str} at {next_day_time}"
        }
        
        # Take the 2 closest slots from current day
        current_day_slots = available_slots[:2]
        
        # Combine with the next day slot
        available_slots = current_day_slots + [next_day_slot]
    else:
        # Fallback if time parsing fails
        day, month, year = date_str.split('-')
        base_date = datetime.datetime(int(year), int(month), int(day))
            
        next_day_date = (base_date + timedelta(days=1)).date()
        next_day_date_str = next_day_date.strftime('%d-%m-%Y')
        
        # Avoid using 12:30 PM in the fallback as well
        next_day_time = "1:00 PM" if time_str == "12:30 PM" else time_str
        
        available_slots = [
            {"date": date_str, "time": "11:30 AM", "formatted_datetime": f"{date_str} at 11:30 AM"},
            {"date": date_str, "time": "2:00 PM", "formatted_datetime": f"{date_str} at 2:00 PM"},
            {"date": next_day_date_str, "time": next_day_time, "formatted_datetime": f"{next_day_date_str} at {next_day_time}"}
        ]
    
    response = {
        "status": "success",
        "unavailable_slot": {
            "date": date_str,
            "time": time_str,
            "formatted_datetime": f"{date_str} at {time_str}"
        },
        "available_slots": available_slots
    }
    
    logger.info(f"Returning available slots: {response}")
    return jsonify(response)

@app.route('/initiate_account_auth', methods=['POST'])
def initiate_account_auth():
    """Initiate account authentication and send OTP."""
    data = request.json or {}
    phone_number = data.get('phone_number')
    
    if not phone_number:
        return jsonify({
            "status": "error",
            "message": "Phone number is required"
        }), 400
    
    # Check if user exists - return error if not found
    if phone_number not in registered_users:
        logger.warning(f"Account authentication attempted for non-existent phone number: {phone_number}")
        return jsonify({
            "status": "error",
            "message": "user not found"
        }), 404
    
    # Generate OTP (in real system, this would be sent via SMS)
    otp = str(random.randint(100000, 999999))
    auth_otps[phone_number] = {
        "otp": otp,
        "expires_at": time.time() + 300  # 5 minutes expiry
    }
    
    logger.info(f"Generated auth OTP {otp} for phone number {phone_number}")
    
    return jsonify({
        "status": "success",
        "message": "Authentication initiated. Please verify with OTP.",
        "otp": otp  # In production, this would be sent via SMS instead
    })

@app.route('/verify_auth_otp', methods=['POST'])
def verify_auth_otp():
    """Verify OTP for account authentication."""
    data = request.json or {}
    phone_number = data.get('phone_number')
    otp = data.get('otp')
    
    if not phone_number or not otp:
        return jsonify({
            "status": "error",
            "message": "Phone number and OTP are required"
        }), 400
    
    # Check if user exists - return error if not found
    if phone_number not in registered_users:
        logger.warning(f"Account verification attempted for non-existent phone number: {phone_number}")
        return jsonify({
            "status": "error",
            "message": "Account not found with this phone number"
        }), 404
    
    # For testing purposes, always succeed with specific OTP
    if otp == "789654" or (phone_number in auth_otps and auth_otps[phone_number]["otp"] == otp):
        # Get user data
        
        # 
        # Clean up used OTP

        user_data = registered_users.get(phone_number)
        if not user_data:
            return jsonify({"error": "User not found"}), 404
        
    # Get the first payment method from the list
        payment_method = user_data["payment_method"][0] if user_data["payment_method"] else None
    
        return jsonify({
        "status": "success",
        "user_name": user_data["user_name"],
        "payment_method": [
            payment_method["card_number"],
            payment_method["exp_month"],
            payment_method["exp_year"],
            payment_method["card_cvv"]
        ] if payment_method else []
    })

    else:
        return jsonify({
            "status": "error",
            "message": "Invalid OTP"
        }), 400

if __name__ == '__main__':
    # Initialize auth_otps dictionary
    auth_otps = {}
    
    logger.info("Starting simplified appointment server on port 8002")
    try:
        app.run(host='0.0.0.0', port=8002, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"Error starting server: {e}") 