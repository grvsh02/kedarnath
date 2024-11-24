import os
import datetime
import json
from django.contrib.auth.decorators import login_required
from main.auth.wrapper import auth_required
from main.models import Attendance, LeaveRequest, Profile, Location, Reimbursement, Payroll
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import date
from django.contrib.auth.models import User
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.conf import settings

@csrf_exempt
@auth_required
def check_in(request):
    try:
        user = request.user
        print(user)
        req = request.POST
        print(req)
        check_in_message = req["check_in_message"]
        location_id = req["location_id"]
        location = Location.objects.get(id=location_id)
        if location.name == "others":
            other_location = req["other_location"]
            attendance = Attendance.objects.create(user=user, check_in_message=check_in_message, location=location,
                                                   other_location=other_location)
        else:
            attendance = Attendance.objects.create(user=user, check_in_message=check_in_message, location=location)
        return JsonResponse({"status": 200, "data": attendance.to_dict()})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Something went wrong"})


@csrf_exempt
@auth_required
def check_out(request):
    try:
        user = request.user
        req = request.POST
        check_out_message = req["check_out_message"]
        attendance = Attendance.objects.filter(user=user).last()
        attendance.check_out = datetime.datetime.now()
        attendance.check_out_message = check_out_message
        attendance.save()
        return JsonResponse({"status": 200, "data": attendance.to_dict()})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Something went wrong"})


@csrf_exempt
@auth_required
def check_attendance(request):
    user = request.user
    print(user.username)
    attendance = Attendance.objects.filter(user=user).last()
    # print(attendance.check_in.date())
    print(date.today())
    if attendance is None or attendance.check_in.date() != date.today():
        locations = Profile.objects.get(user=user).allowed_locations.all()
        locations = [location.to_dict() for location in locations]
        return JsonResponse({"status": 200, "data": {"attendance": None, "locations": locations}})
    return JsonResponse({"status": 200, "data": attendance.to_dict()})


@csrf_exempt
@auth_required
def submit_leave_request(request):
    try:
        user = request.user
        req = json.loads(request.body)
        print(req)
        start_date = req["start_date"]
        end_date = req["end_date"]
        reason = req["reason"]
        start_date = date(start_date["from"]["year"], start_date["from"]["month"], start_date["from"]["day"])
        end_date = date(end_date["to"]["year"], end_date["to"]["month"], end_date["to"]["day"])
        leave_request = LeaveRequest.objects.create(user=user, start_date=start_date, end_date=end_date, reason=reason)
        return JsonResponse({"status": 200, "data": leave_request.to_dict()})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Something went wrong"})


@csrf_exempt
@auth_required
def get_leave_requests(request):
    user = request.user
    leave_requests = LeaveRequest.objects.filter(user=user).order_by("-created_at")
    if leave_requests is None:
        return JsonResponse({"status": 200, "data": []})
    leave_requests = [leave_request.to_dict() for leave_request in leave_requests]
    return JsonResponse({"status": 200, "data": leave_requests})


@csrf_exempt
@auth_required
def me(request):
    user = request.user
    return JsonResponse({"status": 200,
                         "data": {"username": user.username, "email": user.email, "first_name": user.first_name,
                                  "last_name": user.last_name}})

@csrf_exempt
@auth_required
def edit_profile(request):
    user = request.user
    res = json.loads(request.body)
    user_profile = Profile.objects.filter(user=user)
    if "phone" in res:
        user_profile.phone = res["phone"]
    if "address" in res:
        user_profile.address = res["address"]
    if "city" in res:
        user_profile.city = res["city"]
    if "state" in res:
        user_profile.state = res["state"]
    if "country" in res:
        user_profile.country = res["country"]
    if "pincode" in res:
        user_profile.pincode = res["pincode"]
    user_profile.save()

    return JsonResponse({"status": 200, "data": user_profile.to_dict()})


@csrf_exempt
@auth_required
def get_profile(request):
    user = request.user
    try:
        user_profile = Profile.objects.get(user=user)

        attendance = Attendance.objects.filter(user=user).order_by("-check_in")[:7]
        attendance = [att.to_dict() for att in attendance]

        graph_data = {"labels": [], "data": []}
        hours_worked = 0
        avg_hours = 0
        days_worked = 0

        for att in attendance:
            graph_data["labels"].append(att["check_in"].date())
            # Check if check_out exists
            if att["check_out"] is not None:
                worked_hours = att["check_out"].hour - att["check_in"].hour
                graph_data["data"].append(worked_hours)
                hours_worked += max(worked_hours, 0)  # Ensure no negative hours are added
            else:
                graph_data["data"].append(0)  # Use 0 hours for incomplete records

        if graph_data["data"]:
            avg_hours = hours_worked / len(graph_data["data"])
            days_worked = len([data for data in graph_data["data"] if data > 0])

        payroll = Payroll.objects.filter(profile=user_profile).first()
        payroll_data = payroll.to_dict() if payroll else None

        return JsonResponse({
            "status": 200,
            "data": user_profile.to_dict(),
            "graph_data": graph_data,
            "stats_data": {"hours_worked": hours_worked, "avg_hours": avg_hours, "days_worked": days_worked},
            "payroll_data": payroll_data
        })

    except Profile.DoesNotExist:
        return JsonResponse({"status": 404, "message": "Profile not found"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Internal Server Error"})



@csrf_exempt
@auth_required
def admin_dashboard(request):
    user = request.user
    if user.is_superuser:
        total_employees = User.objects.filter(is_superuser=False).count()
        total_employees_present = Attendance.objects.filter(check_in__date=date.today()).count()
        total_employees_absent = total_employees - total_employees_present
        total_late_employee = Attendance.objects.filter(check_in__date=date.today(), check_in__hour__gte=10).count()
        last_7_days_present = Attendance.objects.filter(
            check_in__date__gte=date.today() - datetime.timedelta(days=7)).count()
        last_7_days_absent = total_employees * 7 - last_7_days_present
        last_7_days_late = Attendance.objects.filter(check_in__date__gte=date.today() - datetime.timedelta(days=7),
                                                     check_in__hour__gte=10).count()
        return JsonResponse({"status": 200, "data": {"total_employees": total_employees,
                                                     "total_employees_present": total_employees_present,
                                                     "total_employees_absent": total_employees_absent,
                                                     "total_late_employee": total_late_employee,
                                                     "last_7_days_present": last_7_days_present,
                                                     "last_7_days_absent": last_7_days_absent,
                                                     "last_7_days_late": last_7_days_late}})

    return JsonResponse({"status": 500, "message": "You are not authorized to access this page"})


@csrf_exempt
@auth_required
def get_locations(request):
    user = request.user
    if user.is_superuser:
        locations = Location.objects.all()
        locations = [location.to_dict() for location in locations]
        return JsonResponse({"status": 200, "data": locations})
    return JsonResponse({"status": 500, "message": "You are not authorized to access this page"})



@csrf_exempt
@auth_required
def create_profile(request):
    try: 
        user = request.user
        res = json.loads(request.body)
        print(res)
        user = res["user"]
        phone = res["phone"]
        address = res["address"]
        city = res["city"]
        state = res["state"]
        country = res["country"]
        pincode = res["pincode"]
        # profile = res.FILES["image"]
        job_title = res["job_title"]
        date_of_birth = res["date_of_birth"]
        date_of_joining = res["date_of_joining"]
        if "salary" in res:
            salary = res["salary"]
        else:
            salary = None

        user = User.objects.create_user(username=user, email=user, password=user)
        profile_data = Profile.objects.create(user=user, phone = phone, address=address, city = city, state  = state, country = country, pincode = pincode, job_title = job_title, date_of_birth = date_of_birth, date_of_joining = date_of_joining, salary = salary)
        return JsonResponse({"status": 201, "data": profile_data.to_dict()})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Profile creation unsuccessful"})

@csrf_exempt
@auth_required
def delete_profile(request):
    try:
        user = request.user
        res = json.loads(request.body)
        print(res)
        user = res["user"]

        user = User.objects.get(username=user)
        user.delete()
        return JsonResponse({"status": 200, "message": "Profile deleted successfully"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Profile deletion unsuccessful"})

@csrf_exempt
@auth_required
def create_reimbursement(request):
    try:
        user = request.user
        res = json.loads(request.body)
        amount = res["amount"]
        reason = res["reason"]
        type_of = res["type"]
        expense_date = res["expense_date"]
        reimbursement_data = Reimbursement.objects.create(user=user, amount=amount, reason=reason, type=type_of, expense_date=expense_date)
        return JsonResponse({"status": 201, "data": reimbursement_data.to_dict()})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Please enter correct details!!!"})

@csrf_exempt
@auth_required
def get_reimbursements(request):
    try:
        user = request.user
        reimbersments = Reimbursement.objects.filter(user=user)
        reim_dict = [reim.to_dict() for reim in reimbersments]
        return JsonResponse({"status": 200, "message": reim_dict})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Reimbursement not found"})

@csrf_exempt
@auth_required
def edit_reimbursement(request):
    try:
        user = request.user
        res = json.loads(request.body)
        reimbursement_id = int(res["id"])
        reimbursement = Reimbursement.objects.filter(id=reimbursement_id, user=request.user).first()
        if not reimbursement:
            return JsonResponse({"status": 404, "message": "Reimbursement not found"})
        if "amount" in res:
            reimbursement.amount = res["amount"]
        if "reason" in res:
            reimbursement.reason = res["reason"]
        if "type" in res:
            reimbursement.type = res["type"]
        if "expense_date" in res:
            reimbursement.expense_date = res["expense_date"]
        reimbursement.save()
        return JsonResponse({"status": 200, "message": "Reimbursement updated successfully"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Reimbursement update unsuccessful"})

@csrf_exempt
@auth_required
def create_payroll(request):
    if request.method != "POST":
        return JsonResponse({"status": 405, "message": "Method not allowed"})

    try:
        user = request.user  # Get the logged-in user
        profile = Profile.objects.get(user=user)

        data = json.loads(request.body)
        required_fields = ["basic_salary", "hra", "special_allowance", "tax_deduction", "reimbursement_amount"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return JsonResponse({"status": 400, "message": f"Missing fields: {', '.join(missing_fields)}"})

        payroll = Payroll.objects.create(
            profile=profile,
            basic_salary=data["basic_salary"],
            hra=data["hra"],
            special_allowance=data["special_allowance"],
            tax_deduction=data["tax_deduction"],
            reimbursement_amount=data["reimbursement_amount"],
        )

        payroll.calculate_final_salary()

        return JsonResponse({"status": 201, "data": payroll.to_dict()})

    except Profile.DoesNotExist:
        return JsonResponse({"status": 404, "message": "Profile not found for the logged-in user"})
    except Exception as e:
        print(f"Error in create_payroll: {e}")
        return JsonResponse({"status": 500, "message": "Internal Server Error"})


@csrf_exempt
@auth_required
def generate_employee_pdf(request):
    """
    Generate a PDF for the logged-in user with their Profile and Payroll details.
    """
    try:
        user = request.user 
        pdf_directory = os.path.join(settings.BASE_DIR, "pdfs")
        os.makedirs(pdf_directory, exist_ok=True)

        profile = Profile.objects.filter(user=user).first()
        if not profile:
            return HttpResponse("Profile data not found for the logged-in user.", status=404)

        payroll = Payroll.objects.filter(profile=profile).first()
        if not payroll:
            return HttpResponse("Payroll data not found for the logged-in user.", status=404)

        pdf_path = os.path.join(pdf_directory, f"{user.username}_details.pdf")
        pdf = canvas.Canvas(pdf_path, pagesize=letter)
        pdf.setTitle("Employee Payroll Details")
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(200, 750, "Employee Payroll Details")
        pdf.setFont("Helvetica", 12)

        y_position = 700
        pdf.drawString(50, y_position, f"Name: {user.get_full_name()}")
        y_position -= 20
        pdf.drawString(50, y_position, f"Username: {user.username}")
        y_position -= 20
        pdf.drawString(50, y_position, f"Phone: {profile.phone or 'N/A'}")
        y_position -= 20
        pdf.drawString(50, y_position, f"Address: {profile.address or 'N/A'}")
        y_position -= 20
        pdf.drawString(50, y_position, f"Job Title: {profile.job_title or 'N/A'}")
        y_position -= 20
        pdf.drawString(50, y_position, f"Date of Joining: {profile.date_of_joining or 'N/A'}")
        y_position -= 20

        pdf.setFont("Helvetica-Bold", 14)
        y_position -= 20
        pdf.drawString(50, y_position, "Payroll Details")
        pdf.setFont("Helvetica", 12)
        y_position -= 20
        pdf.drawString(50, y_position, f"Basic Salary: {payroll.basic_salary}")
        y_position -= 20
        pdf.drawString(50, y_position, f"HRA: {payroll.hra}")
        y_position -= 20
        pdf.drawString(50, y_position, f"Special Allowance: {payroll.special_allowance}")
        y_position -= 20
        pdf.drawString(50, y_position, f"Tax Deduction: {payroll.tax_deduction}")
        y_position -= 20
        pdf.drawString(50, y_position, f"Reimbursement Amount: {payroll.reimbursement_amount}")
        y_position -= 20
        pdf.drawString(50, y_position, f"Final Salary: {payroll.final_salary}")
        y_position -= 40

        pdf.setFont("Helvetica-Oblique", 10)
        pdf.drawString(50, 50, "Generated by Employee Management System")
        pdf.save()

        with open(pdf_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/pdf")
            response["Content-Disposition"] = f"attachment; filename={user.username}_details.pdf"
            return response

    except Exception as e:
        print(f"Error generating PDF: {e}")
        return HttpResponse("Error generating PDF.", status=500)
