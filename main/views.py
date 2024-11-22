import datetime
import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import date
from django.contrib.auth.models import User
from main.models import Attendance, LeaveRequest, Profile, Location, Reimbursement, Payroll

@csrf_exempt
def check_in(request):
    try:
        user = request.user
        req = json.loads(request.body)
        check_in_message = req["check_in_message"]
        location_id = req["location_id"]
        location = Location.objects.get(id=location_id)

        if location.name == "others":
            other_location = req["other_location"]
            attendance = Attendance.objects.create(user=user, check_in_message=check_in_message, location=location, other_location=other_location)
        else:
            attendance = Attendance.objects.create(user=user, check_in_message=check_in_message, location=location)
        return JsonResponse({"status": 200, "data": attendance.to_dict()})
    except Location.DoesNotExist:
        return JsonResponse({"status": 404, "message": "Location not found"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Something went wrong"})

@csrf_exempt
def check_out(request):
    try:
        user = request.user
        req = json.loads(request.body)
        check_out_message = req["check_out_message"]
        attendance = Attendance.objects.filter(user=user).last()

        if attendance:
            attendance.check_out = datetime.datetime.now()
            attendance.check_out_message = check_out_message
            attendance.save()
            return JsonResponse({"status": 200, "data": attendance.to_dict()})
        else:
            return JsonResponse({"status": 404, "message": "No check-in record found"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Something went wrong"})

@csrf_exempt
def check_attendance(request):
    user = request.user
    attendance = Attendance.objects.filter(user=user).last()

    if attendance is None or attendance.check_in.date() != date.today():
        locations = Profile.objects.get(user=user).allowed_locations.all()
        locations = [location.to_dict() for location in locations]
        return JsonResponse({"status": 200, "data": {"attendance": None, "locations": locations}})
    
    return JsonResponse({"status": 200, "data": attendance.to_dict()})

@csrf_exempt
def submit_leave_request(request):
    try:
        user = request.user
        req = json.loads(request.body)
        start_date = date(**req["start_date"]["from"])
        end_date = date(**req["end_date"]["to"])
        reason = req["reason"]
        
        leave_request = LeaveRequest.objects.create(user=user, start_date=start_date, end_date=end_date, reason=reason)
        return JsonResponse({"status": 200, "data": leave_request.to_dict()})
    except KeyError:
        return JsonResponse({"status": 400, "message": "Invalid date format"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Something went wrong"})

@csrf_exempt
def get_leave_requests(request):
    user = request.user
    leave_requests = LeaveRequest.objects.filter(user=user).order_by("-created_at")
    leave_requests = [leave_request.to_dict() for leave_request in leave_requests]
    return JsonResponse({"status": 200, "data": leave_requests})

@csrf_exempt
def me(request):
    user = request.user
    return JsonResponse({
        "status": 200,
        "data": {
            "username": user.username, 
            "email": user.email, 
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    })

@csrf_exempt
def edit_profile(request):
    try:
        user = request.user
        res = json.loads(request.body)
        user_profile = Profile.objects.get(user=user)
        
        for field in ["phone", "address", "city", "state", "country", "pincode"]:
            if field in res:
                setattr(user_profile, field, res[field])
        
        user_profile.save()
        return JsonResponse({"status": 200, "data": user_profile.to_dict()})
    except Profile.DoesNotExist:
        return JsonResponse({"status": 404, "message": "Profile not found"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Something went wrong"})

@csrf_exempt
@login_required
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
            worked_hours = (att["check_out"].hour - att["check_in"].hour)
            graph_data["data"].append(worked_hours)
            hours_worked += worked_hours if worked_hours > 0 else 0
        
        if graph_data["data"]:
            avg_hours = hours_worked / len(graph_data["data"])
            days_worked = len(graph_data["data"])

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
def admin_dashboard(request):
    user = request.user
    if user.is_superuser:
        total_employees = User.objects.filter(is_superuser=False).count()
        total_employees_present = Attendance.objects.filter(check_in__date=date.today()).count()
        total_employees_absent = total_employees - total_employees_present
        total_late_employee = Attendance.objects.filter(check_in__date=date.today(), check_in__hour__gte=10).count()
        last_7_days_present = Attendance.objects.filter(check_in__date__gte=date.today() - datetime.timedelta(days=7)).count()
        last_7_days_absent = total_employees * 7 - last_7_days_present
        last_7_days_late = Attendance.objects.filter(check_in__date__gte=date.today() - datetime.timedelta(days=7), check_in__hour__gte=10).count()
        
        return JsonResponse({
            "status": 200,
            "data": {
                "total_employees": total_employees,
                "total_employees_present": total_employees_present,
                "total_employees_absent": total_employees_absent,
                "total_late_employee": total_late_employee,
                "last_7_days_present": last_7_days_present,
                "last_7_days_absent": last_7_days_absent,
                "last_7_days_late": last_7_days_late
            }
        })
    return JsonResponse({"status": 500, "message": "You are not authorized to access this page"})

@csrf_exempt
def get_locations(request):
    user = request.user
    if user.is_superuser:
        locations = Location.objects.all()
        locations = [location.to_dict() for location in locations]
        return JsonResponse({"status": 200, "data": locations})
    return JsonResponse({"status": 500, "message": "You are not authorized to access this page"})

@csrf_exempt
def create_profile(request):
    try: 
        res = json.loads(request.body)
        username = res["user"]
        email = res["user"]
        password = res["user"]

        user = User.objects.create_user(username=username, email=email, password=password)
        profile_data = Profile.objects.create(
            user=user,
            phone=res["phone"],
            address=res["address"],
            city=res["city"],
            state=res["state"],
            country=res["country"],
            pincode=res["pincode"],
            job_title=res["job_title"],
            date_of_birth=res["date_of_birth"],
            date_of_joining=res["date_of_joining"],
            salary=res.get("salary", None)
        )
        return JsonResponse({"status": 201, "data": profile_data.to_dict()}) 
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Profile creation unsuccessful"})

@csrf_exempt
def delete_profile(request):
    try:
        res = json.loads(request.body)
        user = User.objects.get(username=res["user"])
        user.delete()
        return JsonResponse({"status": 200, "message": "Profile deleted successfully"})
    except User.DoesNotExist:
        return JsonResponse({"status": 404, "message": "User not found"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Error while deleting profile"})

@csrf_exempt
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
def get_reimbursements(request):
    try:
        user = request.user
        reimbersments = Reimbursement.objects.filter(user=user)
        reim_dict = [reim.to_dict() for reim in reimbersments]
        return JsonResponse({"status": 200, "message": reim_dict})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Reimbursement get unsuccessful"})


@csrf_exempt
def delete_reimbursement(request):
    try:
        user = request.user
        res = json.loads(request.body)
        reimbursement_id = int(res["id"])
        reimbursement = Reimbursement.objects.filter(id=reimbursement_id, user=request.user).first()
        if not reimbursement:
            return JsonResponse({"status": 404, "message": "Reimbursement not found"})
        reimbursement.delete()
        return JsonResponse({"status": 200, "message": "Reimbursement deleted successfully"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Reimbursement deletion unsuccessful"})


@csrf_exempt
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
def create_payroll(request):
    if request.method != "POST":
        return JsonResponse({"status": 405, "message": "Method not allowed"})
    
    try:
        data = json.loads(request.body)
        required_fields = ["employee_id", "basic_salary", "hra", "special_allowance", "tax_deduction", "reimbursement_amount"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return JsonResponse({"status": 400, "message": f"Missing fields: {', '.join(missing_fields)}"})
    
        employee = User.objects.get(id=data["employee_id"])
        profile = Profile.objects.get(user=employee)
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
    
    except User.DoesNotExist:
        return JsonResponse({"status": 404, "message": "Employee not found"})
    except Profile.DoesNotExist:
        return JsonResponse({"status": 404, "message": "Profile not found for the employee"})
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Internal Server Error"})

