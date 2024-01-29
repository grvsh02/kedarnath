import datetime
import json

from main.models import Attendance, LeaveRequest, Profile, Location
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from datetime import date
from django.contrib.auth.models import User


@csrf_exempt
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
def get_leave_requests(request):
    user = request.user
    leave_requests = LeaveRequest.objects.filter(user=user).order_by("-created_at")
    if leave_requests is None:
        return JsonResponse({"status": 200, "data": []})
    leave_requests = [leave_request.to_dict() for leave_request in leave_requests]
    return JsonResponse({"status": 200, "data": leave_requests})


@csrf_exempt
def me(request):
    user = request.user
    return JsonResponse({"status": 200,
                         "data": {"username": user.username, "email": user.email, "first_name": user.first_name,
                                  "last_name": user.last_name}})


@csrf_exempt
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
def get_profile(request):
    user = request.user
    user_profile = Profile.objects.get(user=user)
    attendance = Attendance.objects.filter(user=user).order_by("-check_in")[0:7]
    attendance = [attendance.to_dict() for attendance in attendance]
    print(attendance)
    graph_data = {"labels": [], "data": []}
    hours_worked = 0
    avg_hours = 0
    days_worked = 0
    for attendance in attendance:
        print(attendance["check_in"], attendance["check_out"])
        graph_data["labels"].append(attendance["check_in"].date())
        try:
            graph_data["data"].append(int(attendance["check_out"].hour - attendance["check_in"].hour))
            hours_worked += int(attendance["check_out"].hour - attendance["check_in"].hour)
        except:
            graph_data["data"].append(0)
        print(graph_data)
        avg_hours = hours_worked / len(graph_data["data"])
        days_worked = len(graph_data["data"])
    return JsonResponse({"status": 200, "data": user_profile.to_dict(), "graph_data": graph_data,
                         "stats_data": {"hours_worked": hours_worked, "avg_hours": avg_hours,
                                        "days_worked": days_worked}})


@csrf_exempt
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
        profiledata = Profile.objects.create(user=user, phone = phone, address=address, city = city, state  = state, country = country, pincode = pincode, job_title = job_title, date_of_birth = date_of_birth, date_of_joining = date_of_joining, salary = salary)
        return JsonResponse({"status": 201, "data": profiledata.to_dict()}) 
    except Exception as e:
        print(e)
        return JsonResponse({"status": 500, "message": "Profile creation unsuccessful"})



@csrf_exempt
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
