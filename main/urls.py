from django.urls import re_path as url
from main.auth import auth
from main import views

urlpatterns = [
    url(r'^logout/$', auth.logout, name="logout"),
    url(r'^login/$', auth.login, name="login"),
    url(r'^check/in/$', views.check_in, name="signup"),
    url(r'^check/out/$', views.check_out, name="signup"),
    url(r'^attendance/status/$', views.check_attendance, name="signup"),
    url(r'^leave/request/$', views.submit_leave_request, name="signup"),
    url(r'^leave/requests/$', views.get_leave_requests, name="signup"),
    url(r'me/$', views.me, name='me'),
    # url(r'^signup/$', views.signup, name="signup"),
    url(r'^me/profile/edit/$', views.edit_profile, name="Edit Profile"),
    url(r'^me/profile/get/$', views.get_profile, name="Get profile"),
    url(r'^locations/get/$', views.get_locations, name="Get locations"),
    # url(r'^locations/add/$', views.add_location, name="Add location"),
    # url(r'^locations/edit/$', views.edit_location, name="Edit location"),
    # url(r'^locations/delete/$', views.delete_location, name="Delete location"),
    # url(r'^location/get/$', views.get_location, name="Get location"),
    url(r'^get-token/$', auth.get_token, name="Get token"),
    url(r'^me/profile/create/$', views.create_profile, name="Create Profile"),
    url(r'^me/profile/delete/$', views.delete_profile, name="Delete Profile"),
    url(r'^payroll/create/$', views.create_payroll, name="Create Payroll"),
    url(r'^create_reimbursement/$', views.create_reimbursement, name="create_reimbursement"),
    url(r'^reimbursement/get/$', views.get_reimbursements, name="Get reimbursement"),
    url(r'^reimbursement/edit/$', views.edit_reimbursement, name="Edit reimbursement"),
    url(r'^profile/get/pdf/$', views.generate_employee_pdf, name="Profile PDF"),

]
