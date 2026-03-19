from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
import math

app = FastAPI(
    title="MediCare Clinic API",
    description="Medical Appointment System — Final Project Q1–Q20",
    version="1.0.0"
)

# ==============================================================
# T2 — IN-MEMORY DATA
# ==============================================================

doctors = [
    {"id": 1, "name": "Dr. Aisha Kapoor",  "specialization": "Cardiologist",  "fee": 800, "experience_years": 15, "is_available": True},
    {"id": 2, "name": "Dr. Rahul Mehta",   "specialization": "Dermatologist",  "fee": 500, "experience_years": 8,  "is_available": True},
    {"id": 3, "name": "Dr. Priya Nair",    "specialization": "Pediatrician",   "fee": 400, "experience_years": 12, "is_available": False},
    {"id": 4, "name": "Dr. Sameer Joshi",  "specialization": "General",        "fee": 300, "experience_years": 5,  "is_available": True},
    {"id": 5, "name": "Dr. Neha Singh",    "specialization": "Cardiologist",   "fee": 900, "experience_years": 20, "is_available": True},
    {"id": 6, "name": "Dr. Vikram Bose",   "specialization": "Dermatologist",  "fee": 450, "experience_years": 10, "is_available": False},
]

appointments = []
appt_counter = 1
doctor_id_counter = 7


# ==============================================================
# PYDANTIC MODELS  
# ==============================================================

class AppointmentRequest(BaseModel):
    patient_name: str = Field(..., min_length=2, description="Patient full name")
    doctor_id: int = Field(..., gt=0, description="Valid doctor ID")
    date: str = Field(..., min_length=8, description="Date e.g. 2025-06-10 10:00")
    reason: str = Field(..., min_length=5, description="Reason for visit")
    appointment_type: str = Field("in-person", description="in-person | video | emergency")
    senior_citizen: bool = Field(False, description="15% extra discount if True")  # Q9


class NewDoctor(BaseModel):
    name: str = Field(..., min_length=2)
    specialization: str = Field(..., min_length=2)
    fee: int = Field(..., gt=0)
    experience_years: int = Field(..., gt=0)
    is_available: bool = Field(True)


# ==============================================================
# HELPER FUNCTIONS
# ==============================================================

def find_doctor(doctor_id: int):
    return next((d for d in doctors if d["id"] == doctor_id), None)


def find_appointment(appt_id: int):
    return next((a for a in appointments if a["id"] == appt_id), None)


def calculate_fee(base_fee: int, appointment_type: str, senior_citizen: bool) -> dict:
    """
    Q7: video = 80%, emergency = 150%, in-person = 100%
    Q9: senior_citizen applies extra 15% discount after type calculation
    """
    t = appointment_type.lower()
    if t == "video":
        calculated = base_fee * 0.80
    elif t == "emergency":
        calculated = base_fee * 1.50
    else:
        calculated = float(base_fee)

    original_fee = round(calculated, 2)
    final_fee = round(calculated * 0.85, 2) if senior_citizen else original_fee
    return {"original_fee": original_fee, "final_fee": final_fee}


def filter_doctors_logic(specialization, max_fee, min_experience, is_available):
    """Q10 — all checks use 'is not None'"""
    result = doctors.copy()
    if specialization is not None:
        result = [d for d in result if d["specialization"].lower() == specialization.lower()]
    if max_fee is not None:
        result = [d for d in result if d["fee"] <= max_fee]
    if min_experience is not None:
        result = [d for d in result if d["experience_years"] >= min_experience]
    if is_available is not None:
        result = [d for d in result if d["is_available"] == is_available]
    return result



# HOME
# ==============================================================

@app.get("/", tags=["General"])
def home():
    return {"message": "Welcome to MediCare Clinic"}




#SUMMARY
@app.get("/doctors/summary", tags=["Doctors"])
def doctor_summary():
    total = len(doctors)
    available_count = sum(1 for d in doctors if d["is_available"])
    most_experienced = max(doctors, key=lambda d: d["experience_years"])["name"] if doctors else None
    cheapest_fee = min(d["fee"] for d in doctors) if doctors else None
    spec_count = {}
    for d in doctors:
        spec_count[d["specialization"]] = spec_count.get(d["specialization"], 0) + 1
    return {
        "total_doctors": total,
        "available_count": available_count,
        "most_experienced_doctor": most_experienced,
        "cheapest_consultation_fee": cheapest_fee,
        "doctors_per_specialization": spec_count
    }


# Q10 — FILTER
@app.get("/doctors/filter", tags=["Doctors"])
def filter_doctors(
    specialization: Optional[str] = Query(None),
    max_fee: Optional[int] = Query(None),
    min_experience: Optional[int] = Query(None),
    is_available: Optional[bool] = Query(None)
):
    result = filter_doctors_logic(specialization, max_fee, min_experience, is_available)
    return {"total": len(result), "doctors": result}


# Q16 — SEARCH
@app.get("/doctors/search", tags=["Doctors"])
def search_doctors(keyword: str = Query(..., description="Search name or specialization")):
    kw = keyword.lower()
    result = [d for d in doctors if kw in d["name"].lower() or kw in d["specialization"].lower()]
    if not result:
        return {"message": f"No doctors found matching '{keyword}'", "total_found": 0, "results": []}
    return {"total_found": len(result), "results": result}


# Q17 — SORT
@app.get("/doctors/sort", tags=["Doctors"])
def sort_doctors(
    sort_by: str = Query("fee", description="fee | name | experience_years"),
    order: str = Query("asc", description="asc | desc")
):
    valid = ["fee", "name", "experience_years"]
    if sort_by not in valid:
        raise HTTPException(400, detail=f"sort_by must be one of {valid}")
    if order not in ["asc", "desc"]:
        raise HTTPException(400, detail="order must be 'asc' or 'desc'")
    sorted_list = sorted(doctors, key=lambda d: d[sort_by], reverse=(order == "desc"))
    return {"sort_by": sort_by, "order": order, "total": len(sorted_list), "doctors": sorted_list}


# Q18 — PAGINATION
@app.get("/doctors/page", tags=["Doctors"])
def paginate_doctors(
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1)
):
    total = len(doctors)
    total_pages = math.ceil(total / limit)
    start = (page - 1) * limit
    return {
        "page": page,
        "limit": limit,
        "total_records": total,
        "total_pages": total_pages,
        "doctors": doctors[start: start + limit]
    }


# Q20 — BROWSE (filter → sort → paginate)
@app.get("/doctors/browse", tags=["Doctors"])
def browse_doctors(
    keyword: Optional[str] = Query(None),
    sort_by: str = Query("fee"),
    order: str = Query("asc"),
    page: int = Query(1, ge=1),
    limit: int = Query(4, ge=1)
):
    valid = ["fee", "name", "experience_years"]
    if sort_by not in valid:
        raise HTTPException(400, detail=f"sort_by must be one of {valid}")
    if order not in ["asc", "desc"]:
        raise HTTPException(400, detail="order must be 'asc' or 'desc'")

    result = doctors.copy()
    # Step 1 — filter/search
    if keyword:
        kw = keyword.lower()
        result = [d for d in result if kw in d["name"].lower() or kw in d["specialization"].lower()]
    # Step 2 — sort
    result = sorted(result, key=lambda d: d[sort_by], reverse=(order == "desc"))
    # Step 3 — paginate
    total = len(result)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start = (page - 1) * limit
    return {
        "keyword": keyword, "sort_by": sort_by, "order": order,
        "page": page, "limit": limit,
        "total_records": total, "total_pages": total_pages,
        "doctors": result[start: start + limit]
    }


# Q2 — GET ALL DOCTORS
@app.get("/doctors", tags=["Doctors"])
def get_all_doctors():
    return {
        "total": len(doctors),
        "available_count": sum(1 for d in doctors if d["is_available"]),
        "doctors": doctors
    }


# Q11 — POST /doctors  (201 + duplicate check)
@app.post("/doctors", status_code=201, tags=["Doctors"])
def add_doctor(doctor: NewDoctor):
    global doctor_id_counter
    if any(d["name"].lower() == doctor.name.lower() for d in doctors):
        raise HTTPException(400, detail=f"Doctor '{doctor.name}' already exists")
    new = {
        "id": doctor_id_counter,
        "name": doctor.name,
        "specialization": doctor.specialization,
        "fee": doctor.fee,
        "experience_years": doctor.experience_years,
        "is_available": doctor.is_available
    }
    doctors.append(new)
    doctor_id_counter += 1
    return {"message": "Doctor added successfully", "doctor": new}


# Q3 — GET /doctors/{doctor_id}  ⚠️ VARIABLE ROUTE — below all fixed routes
@app.get("/doctors/{doctor_id}", tags=["Doctors"])
def get_doctor(doctor_id: int):
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(404, detail=f"Doctor with ID {doctor_id} not found")
    return doctor


# Q12 — PUT /doctors/{doctor_id}
@app.put("/doctors/{doctor_id}", tags=["Doctors"])
def update_doctor(
    doctor_id: int,
    fee: Optional[int] = Query(None, gt=0),
    is_available: Optional[bool] = Query(None)
):
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(404, detail=f"Doctor with ID {doctor_id} not found")
    if fee is not None:
        doctor["fee"] = fee
    if is_available is not None:
        doctor["is_available"] = is_available
    return {"message": "Doctor updated", "doctor": doctor}


# Q13 — DELETE /doctors/{doctor_id}
@app.delete("/doctors/{doctor_id}", tags=["Doctors"])
def delete_doctor(doctor_id: int):
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(404, detail=f"Doctor with ID {doctor_id} not found")
    active = [a for a in appointments if a["doctor_id"] == doctor_id and a["status"] == "scheduled"]
    if active:
        raise HTTPException(400, detail="Cannot delete doctor with active scheduled appointments")
    doctors.remove(doctor)
    return {"message": f"Doctor '{doctor['name']}' deleted successfully"}


# ==============================================================
# ⚠️  ALL FIXED /appointments ROUTES MUST BE ABOVE /{appointment_id}
# ==============================================================

# Q4 — GET ALL APPOINTMENTS
@app.get("/appointments", tags=["Appointments"])
def get_all_appointments():
    return {"total": len(appointments), "appointments": appointments}


# Q15 — ACTIVE APPOINTMENTS
@app.get("/appointments/active", tags=["Appointments"])
def get_active_appointments():
    active = [a for a in appointments if a["status"] in ["scheduled", "confirmed"]]
    return {"total": len(active), "appointments": active}


# Q19 — SEARCH APPOINTMENTS
@app.get("/appointments/search", tags=["Appointments"])
def search_appointments(patient_name: str = Query(...)):
    kw = patient_name.lower()
    result = [a for a in appointments if kw in a["patient_name"].lower()]
    if not result:
        return {"message": f"No appointments found for '{patient_name}'", "total_found": 0, "results": []}
    return {"total_found": len(result), "results": result}


# Q19 — SORT APPOINTMENTS
@app.get("/appointments/sort", tags=["Appointments"])
def sort_appointments(
    sort_by: str = Query("final_fee", description="final_fee | date"),
    order: str = Query("asc")
):
    valid = ["final_fee", "date"]
    if sort_by not in valid:
        raise HTTPException(400, detail=f"sort_by must be one of {valid}")
    if order not in ["asc", "desc"]:
        raise HTTPException(400, detail="order must be 'asc' or 'desc'")
    sorted_list = sorted(appointments, key=lambda a: a[sort_by], reverse=(order == "desc"))
    return {"sort_by": sort_by, "order": order, "total": len(sorted_list), "appointments": sorted_list}


# Q19 — PAGINATE APPOINTMENTS
@app.get("/appointments/page", tags=["Appointments"])
def paginate_appointments(
    page: int = Query(1, ge=1),
    limit: int = Query(3, ge=1)
):
    total = len(appointments)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start = (page - 1) * limit
    return {
        "page": page, "limit": limit,
        "total_records": total, "total_pages": total_pages,
        "appointments": appointments[start: start + limit]
    }


# Q8 — POST /appointments  (books + calculates fee)
@app.post("/appointments", status_code=201, tags=["Appointments"])
def book_appointment(request: AppointmentRequest):
    global appt_counter
    doctor = find_doctor(request.doctor_id)
    if not doctor:
        raise HTTPException(404, detail=f"Doctor with ID {request.doctor_id} not found")
    if not doctor["is_available"]:
        raise HTTPException(400, detail=f"Dr. {doctor['name']} is currently not available")

    fees = calculate_fee(doctor["fee"], request.appointment_type, request.senior_citizen)

    appointment = {
        "id": appt_counter,
        "patient_name": request.patient_name,
        "doctor_id": request.doctor_id,
        "doctor_name": doctor["name"],
        "specialization": doctor["specialization"],
        "date": request.date,
        "reason": request.reason,
        "appointment_type": request.appointment_type,
        "senior_citizen": request.senior_citizen,
        "original_fee": fees["original_fee"],
        "final_fee": fees["final_fee"],
        "status": "scheduled"
    }
    appointments.append(appointment)
    appt_counter += 1
    doctor["is_available"] = False
    return {"message": "Appointment booked successfully", "appointment": appointment}


# Q14 — CONFIRM
@app.post("/appointments/{appointment_id}/confirm", tags=["Appointments"])
def confirm_appointment(appointment_id: int):
    appt = find_appointment(appointment_id)
    if not appt:
        raise HTTPException(404, detail=f"Appointment {appointment_id} not found")
    if appt["status"] != "scheduled":
        raise HTTPException(400, detail=f"Only scheduled appointments can be confirmed (current: {appt['status']})")
    appt["status"] = "confirmed"
    return {"message": "Appointment confirmed", "appointment": appt}


# Q14 — CANCEL
@app.post("/appointments/{appointment_id}/cancel", tags=["Appointments"])
def cancel_appointment(appointment_id: int):
    appt = find_appointment(appointment_id)
    if not appt:
        raise HTTPException(404, detail=f"Appointment {appointment_id} not found")
    if appt["status"] == "cancelled":
        raise HTTPException(400, detail="Appointment is already cancelled")
    appt["status"] = "cancelled"
    doctor = find_doctor(appt["doctor_id"])
    if doctor:
        doctor["is_available"] = True
    return {"message": "Appointment cancelled. Doctor is now available.", "appointment": appt}


# Q15 — COMPLETE
@app.post("/appointments/{appointment_id}/complete", tags=["Appointments"])
def complete_appointment(appointment_id: int):
    appt = find_appointment(appointment_id)
    if not appt:
        raise HTTPException(404, detail=f"Appointment {appointment_id} not found")
    if appt["status"] != "confirmed":
        raise HTTPException(400, detail=f"Only confirmed appointments can be completed (current: {appt['status']})")
    appt["status"] = "completed"
    doctor = find_doctor(appt["doctor_id"])
    if doctor:
        doctor["is_available"] = True
    return {"message": "Appointment completed successfully", "appointment": appt}


# Q15 — BY DOCTOR
@app.get("/appointments/by-doctor/{doctor_id}", tags=["Appointments"])
def appointments_by_doctor(doctor_id: int):
    doctor = find_doctor(doctor_id)
    if not doctor:
        raise HTTPException(404, detail=f"Doctor with ID {doctor_id} not found")
    result = [a for a in appointments if a["doctor_id"] == doctor_id]
    return {"doctor_name": doctor["name"], "total_appointments": len(result), "appointments": result}
