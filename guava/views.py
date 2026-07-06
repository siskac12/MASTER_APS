from django.shortcuts import render, redirect
from . import models
from datetime import datetime
import calendar
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login , logout, authenticate
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from django.forms import DateInput
from django.db.models import F,Q,Sum,Value
import math
from weasyprint import HTML
from django.template.loader import render_to_string
import tempfile
from django.urls import reverse
from io import BytesIO
from django.utils.timezone import now
from django.shortcuts import render
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import json


# # Authentication Views
# def login_view(request):
#     if request.user.is_authenticated:
#         group = None
#         if request.user.groups.exists():
#             group = request.user.groups.all()[0].name

#         if group == 'inspection':
#             return redirect('read_partner')
#         elif group in ['admin', 'owner']:
#             return redirect('base')
#         else:
#             return redirect('read_production')
#     else:
#         return render(request, "base/login.html")


# def perform_login(request):
#     if request.method != "POST":
#         return HttpResponse("Method not Allowed")
#     else:
#         username_login = request.POST['username']
#         password_login = request.POST['password']
#         user_obj = authenticate(request, username=username_login, password=password_login)

#         if user_obj is not None:
#             login(request, user_obj)
#             messages.success(request, "Login success")

#             if user_obj.groups.filter(name='admin').exists() or user_obj.groups.filter(name='owner').exists():
#                 return redirect("base")
#             elif user_obj.groups.filter(name='inspection').exists():
#                 return redirect("read_partner")
#             elif user_obj.groups.filter(name='production').exists():
#                 return redirect('read_production')
#             else:
#                 return redirect('login')
#         else:
#             messages.error(request, "Invalid username or password!")
#             return redirect("login")


# @login_required(login_url="login")
# def logout_view(request):
#     logout(request)
#     messages.info(request, "Successfully logged out")
#     return redirect('login')


# @login_required(login_url="login")
# def perform_logout(request):
#     logout(request)
#     return redirect("login")

# @login_required(login_url="login")
# @role_required(["owner", 'admin'])
# def base(request):
#     sale_details = models.SaleDetail.objects.all()
#     local_harvest_details = models.LocalHarvestDetail.objects.all()
#     partner_harvest_details = models.PartnerHarvestDetail.objects.all()
#     commodities = models.Commodity.objects.all()
#     commodity_dict = {i: 0 for i in commodities}

#     for local in local_harvest_details:
#         commodity = local.commodity_id
#         commodity_dict[commodity] = commodity_dict.get(commodity, 0) + local.quantity

#     for partner in partner_harvest_details:
#         commodity = partner.commodity_id
#         commodity_dict[commodity] = commodity_dict.get(commodity, 0) + partner.quantity

#     list_commodities = list(commodity_dict.keys())
#     list_quantities = list(commodity_dict.values())

#     if request.method == 'GET':
#         return render(request, 'base/dashboard.html', {
#             'list_commodities': list_commodities,
#             'list_quantities': list_quantities,
#         })

#     else:
#         inp = request.POST['chart']
#         list_markets = []
#         list_quantities = []

#         if inp == 'Product':
#             for i in sale_details:
#                 if i.sale_id.market_id is not None and i.commodity_quantity:
#                     list_markets.append(i.sale_id.market_id.market_name)
#                     list_quantities.append(i.commodity_quantity)

#         elif inp == 'Commodity':
#             for i in sale_details:
#                 if i.sale_id.market_id is not None and i.product_quantity:
#                     list_markets.append(i.sale_id.market_id.market_name)
#                     list_quantities.append(i.product_quantity)

#         market_dict = {}
#         for a, b in zip(list_markets, list_quantities):
#             market_dict[a] = market_dict.get(a, 0) + b

#         final_markets = list(market_dict.keys())
#         final_quantities = list(market_dict.values())

#         return render(request, 'base/dashboard.html', {
#             'list_commodities': list_commodities,
#             'list_quantities': list_quantities,
#             'list_markets': final_markets,
#             'list_market_quantities': final_quantities,
#         })


# @login_required(login_url="login")
# @role_required(["owner", 'admin','inspection'])
# def read_partner(request):
#     all_partners = models.Partner.objects.all().order_by('start_date')
#     if not all_partners.exists():
#         messages.error(request, "No Partner Data Found!")
#     return render(request, 'partner/read_partner.html', {
#         'all_partners': all_partners
#     })





# @login_required(login_url="login")
# def activity_logs(request):
#     logs = models.ActivityLog.objects.all().order_by('-timestamp') 
#     return render(request, 'log/activity_log.html', {'logs': logs})

# @login_required
# @role_required(['owner'])  
# def delete_log(request, id):
#     try:
#         log = models.ActivityLog.objects.get(id=id)
#         log.delete()
#         messages.success(request, "Log berhasil dihapus.")
#     except models.ActivityLog.DoesNotExist:
#         messages.error(request, "Log tidak ditemukan.")
#     return redirect('activity_logs') 

