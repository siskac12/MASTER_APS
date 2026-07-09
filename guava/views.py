from django.shortcuts import render, redirect
from . import models
from datetime import datetime, timedelta
import calendar
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import login , logout, authenticate
from django.contrib.auth.decorators import login_required
from .decorators import role_required
from django.forms import DateInput
from django.db.models import F,Q,Sum,Value
import math
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
def login_view(request):
    if request.user.is_authenticated:
        group = None
        if request.user.groups.exists():
            group = request.user.groups.all()[0].name

        if group == 'inspection':
            return redirect('read_partner')
        elif group in ['admin', 'owner']:
            return redirect('base')
        else:
            return redirect('create_partner')
    else:
        return render(request, "base/login.html")


def perform_login(request):
    if request.method != "POST":
        return HttpResponse("Method not Allowed")
    else:
        username_login = request.POST['username']
        password_login = request.POST['password']
        user_obj = authenticate(request, username=username_login, password=password_login)

        if user_obj is not None:
            login(request, user_obj)
            messages.success(request, "Login success")

            if user_obj.groups.filter(name='admin').exists() or user_obj.groups.filter(name='owner').exists():
                return redirect("base")
            elif user_obj.groups.filter(name='inspection').exists():
                return redirect("read_partner")
            elif user_obj.groups.filter(name='production').exists():
                return redirect('read_production')
            else:
                return redirect('login')
        else:
            messages.error(request, "Invalid username or password!")
            return redirect("login")


@login_required(login_url="login")
def logout_view(request):
    logout(request)
    messages.info(request, "Successfully logged out")
    return redirect('login')


@login_required(login_url="login")
def perform_logout(request):
    logout(request)
    return redirect("login")

@login_required(login_url="login")
@role_required(["owner", 'admin'])
def base(request):
    local_harvest_details = models.LocalHarvestDetail.objects.all()
    partner_harvest_details = models.PartnerHarvestDetail.objects.all()
    commodities = models.Commodity.objects.all()
    commodity_dict = {i: 0 for i in commodities}

    for local in local_harvest_details:
        commodity = local.commodity_id
        commodity_dict[commodity] = commodity_dict.get(commodity, 0) + local.quantity

    for partner in partner_harvest_details:
        commodity = partner.commodity_id
        commodity_dict[commodity] = commodity_dict.get(commodity, 0) + partner.quantity

    list_commodities = list(commodity_dict.keys())
    list_quantities = list(commodity_dict.values())

    if request.method == 'GET':
        return render(request, 'base/dashboard.html', {
            'list_commodities': list_commodities,
            'list_quantities': list_quantities,
        })

    else:
        inp = request.POST['chart']
        list_markets = []
        list_quantities = []

        # if inp == 'Product':
        #     for i in sale_details:
        #         if i.sale_id.market_id is not None and i.commodity_quantity:
        #             list_markets.append(i.sale_id.market_id.market_name)
        #             list_quantities.append(i.commodity_quantity)

        # elif inp == 'Commodity':
        #     for i in sale_details:
        #         if i.sale_id.market_id is not None and i.product_quantity:
        #             list_markets.append(i.sale_id.market_id.market_name)
        #             list_quantities.append(i.product_quantity)

        market_dict = {}
        for a, b in zip(list_markets, list_quantities):
            market_dict[a] = market_dict.get(a, 0) + b

        final_markets = list(market_dict.keys())
        final_quantities = list(market_dict.values())

        return render(request, 'base/dashboard.html', {
            'list_commodities': list_commodities,
            'list_quantities': list_quantities,
            'list_markets': final_markets,
            'list_market_quantities': final_quantities,
        })

@login_required(login_url="login")
@role_required(["owner", 'admin'])
def create_partner(request):
    if request.method == "GET":
        return render(request, 'partner/create_partner.html')
    else:
        partner_name = request.POST["partner_name"].lower()
        partner_obj = models.Partner.objects.filter(partner_name=partner_name)

        if partner_obj.exists():
            messages.error(request, "Partner name already exists")
            return redirect("create_partner")

        land_area = request.POST.get("land_area") or None

        data = models.Partner(
            partner_name=request.POST["partner_name"].lower(),
            partner_address=request.POST.get("partner_address"),
            partner_phone=request.POST["partner_phone"],
            start_date=request.POST["start_date"],
            contract_duration=request.POST["contract_duration"],
            land_area=land_area,
            email=request.POST["email"],
            dokumen=request.FILES.get("dokumen"),
            inspection_notes=request.POST.get("inspection_notes"),
            partner_status=request.POST["partner_status"],
        )

        data.save()

        models.ActivityLog.objects.create(
            user=request.user,
            action="Add Partner",
            description=f"Added new partner: {data.partner_name}, status: {data.partner_status}, contract {data.contract_duration} months."
        )

        messages.success(request, "Partner successfully added!")
        return redirect("read_partner")

@login_required(login_url="login")
@role_required(["owner", 'admin','inspection'])
def read_partner(request):
    all_partners = models.Partner.objects.all().order_by('start_date')
    if not all_partners.exists():
        messages.error(request, "No Partner Data Found!")
    return render(request, 'partner/read_partner.html', {
        'all_partners': all_partners
    })

@login_required(login_url="login")
@role_required(["owner", "admin"])
def update_partner(request, id):
    try:
        partner_obj = models.Partner.objects.get(partner_id=id)
    except models.Partner.DoesNotExist:
        messages.error(request, "Partner not found!")
        return redirect("read_partner")

    if request.method == "GET":
        return render(request, "partner/update_partner.html", {
            "partner_obj": partner_obj,
            "start_date": partner_obj.start_date.strftime("%Y-%m-%d"),
        })

    partner_name = request.POST["partner_name"].lower()

    if models.Partner.objects.filter(partner_name=partner_name).exclude(partner_id=id).exists():
        messages.error(request, "Partner name already exists!")
        return redirect("update_partner", id=id)

    land_area = request.POST.get("land_area") or None

    old_status = partner_obj.partner_status

    partner_obj.partner_name = partner_name
    partner_obj.partner_address = request.POST.get("partner_address")
    partner_obj.partner_phone = request.POST["partner_phone"]
    partner_obj.start_date = request.POST["start_date"]
    partner_obj.contract_duration = request.POST["contract_duration"]
    partner_obj.land_area = land_area
    partner_obj.email = request.POST["email"]
    partner_obj.inspection_notes = request.POST.get("inspection_notes")
    partner_obj.partner_status = request.POST["partner_status"]

    
    if request.FILES.get("dokumen"):
        partner_obj.dokumen = request.FILES["dokumen"]

    partner_obj.save()

    models.ActivityLog.objects.create(
        user=request.user,
        action="Update Partner",
        description=(
            f"Updated partner: {partner_obj.partner_name}. "
            f"Status: {old_status} → {partner_obj.partner_status}"
        )
    )

    messages.success(request, "Partner successfully updated!")
    return redirect("read_partner")

@login_required(login_url="login")
@role_required(["owner"])
def delete_partner(request, id):
    partner_obj = models.Partner.objects.get(partner_id=id)
    name = partner_obj.partner_name
    address = partner_obj.partner_address
    phone = partner_obj.partner_phone

    models.ActivityLog.objects.create(
        user=request.user,
        action="Delete Partner",
        description=f"Deleted partner: {name}, Address: {address}, Phone: {phone}."
    )

    partner_obj.delete()
    messages.success(request, "Partner successfully deleted!")
    return redirect('read_partner')

@login_required(login_url='login')
@role_required(['owner'])
def create_grade(request):
    if request.method == "GET":
        return render(request, 'grade/create_grade.html')
    else:
        grade_name = request.POST["grade_name"]
        grade_obj = models.Grade.objects.filter(grade_name=grade_name)

        if grade_obj.exists():
            messages.error(request, "Grade name already exists!")
            return redirect("create_grade")
        else:
            description = request.POST["grade_description"]

            data = models.Grade(
                grade_name=grade_name,
                grade_description=description,
            )
            data.save()
            messages.success(request, "Grade successfully added!")

            models.ActivityLog(
                user=request.user,
                action="Add Grade",
                description=f"Added new grade: {data.grade_name} - {data.grade_description}."
            ).save()

        return redirect("read_grade")

@login_required(login_url='login')
@role_required(['owner', 'admin', 'inspection'])
def read_grade(request):
    gradeobj = models.Grade.objects.all()
    return render(request, 'grade/read_grade.html', {'gradeobj': gradeobj})

@login_required(login_url='login')
@role_required(['owner'])
def update_grade(request, id):
    try:
        grade_obj = models.Grade.objects.get(grade_id=id)
    except models.Grade.DoesNotExist:
        messages.error(request, "Grade not found!")
        return redirect('read_grade')

    if request.method == "GET":
        return render(request, 'grade/update_grade.html', {
            'gradeobj': grade_obj,
        })
    else:
        grade_name = request.POST["grade_name"]
        if models.Grade.objects.filter(grade_name=grade_name).exclude(grade_id=id).exists():
            messages.error(request, "Grade name already exists!")
            return render(request, 'grade/update_grade.html', {
                'gradeobj': grade_obj,
            })

        old_name = grade_obj.grade_name
        old_desc = grade_obj.grade_description

        grade_obj.grade_name = request.POST["grade_name"]
        grade_obj.grade_description = request.POST["grade_description"]
        grade_obj.save()

        models.ActivityLog(
            user=request.user,
            action="Update Grade",
            description=f"Updated grade from '{old_name} - {old_desc}' \n to '{grade_obj.grade_name} - {grade_obj.grade_description}'."
        ).save()

        messages.success(request, "Grade successfully updated!")
        return redirect('read_grade')

@login_required(login_url='login')
@role_required(['owner'])
def delete_grade(request, id):
    grade_obj = models.Grade.objects.get(grade_id=id)
    grade_name = grade_obj.grade_name
    grade_description = grade_obj.grade_description

    grade_obj.delete()

    models.ActivityLog(
        user=request.user,
        action="Delete Grade",
        description=f"Deleted grade: {grade_name} - {grade_description}."
    ).save()

    messages.success(request, "Grade successfully deleted!")
    return redirect('read_grade')

@login_required(login_url='login')
@role_required(['owner'])
def create_commodity(request):
    grade_obj = models.Grade.objects.all()
    
    if request.method == 'GET':
        return render(request, 'commodity/create_commodity.html', {
            'grade_obj': grade_obj
        })
    
    else:
        grade_name = request.POST['grade_name']
        commodity_name = request.POST['commodity_name']
        shelf_life = request.POST['shelf_life']
        purchase_price = request.POST['purchase_price']
        selling_price = request.POST['selling_price']

        commodity_obj = models.Commodity.objects.filter(
            commodity_name=commodity_name,
            grade_id__grade_name=grade_name
        )

        if commodity_obj.exists():
            messages.error(request, "Commodity already exists!")
        
        else:
            grade_instance = models.Grade.objects.get(grade_name=grade_name)
            data = models.Commodity(
                grade_id=grade_instance,
                commodity_name=commodity_name,
                shelf_life = shelf_life,
                purchase_price=purchase_price,
                selling_price=selling_price,
            )
            data.save()

            models.ActivityLog(
                user=request.user,
                action="Add Commodity",
                description=(
                    f"Added new commodity: {data.commodity_name}, "
                    f"Grade {data.grade_id.grade_name}, "
                    f"Purchase {data.purchase_price}, "
                    f"Selling {data.selling_price}."
                )
            ).save()

            messages.success(request, "Commodity has been successfully added!")

        return redirect('read_commodity')

@login_required(login_url='login')
@role_required(['owner', 'admin', 'inspection'])
def read_commodity(request):
    commodity_obj = models.Commodity.objects.all()
    if not commodity_obj.exists():
        messages.error(request, "No commodity data found!")

    return render(request, 'commodity/read_commodity.html', {
        'commodity_obj': commodity_obj
    })

@login_required(login_url='login')
@role_required(['owner'])
def update_commodity(request, id):
    grade_obj = models.Grade.objects.all()
    commodity = models.Commodity.objects.get(commodity_id=id)
    grade_name = commodity.grade_id.grade_name

    if request.method == 'GET':
        return render(request, 'commodity/update_commodity.html', {
            'commodity': commodity,
            'grade_name': grade_name,
            'grade_obj': grade_obj,
            'id': id,
        })

    else:
        new_grade_name = request.POST['grade_name']
        new_commodity_name = request.POST['commodity_name']
        new_shelf_life = request.POST['shelf_life']
        new_purchase_price = request.POST['purchase_price']
        new_selling_price = request.POST['selling_price']

        commodity_obj = models.Commodity.objects.filter(
            commodity_name=new_commodity_name,
            grade_id__grade_name=new_grade_name
        )
        if commodity_obj.exists() and (
            commodity.commodity_name != new_commodity_name 
            or commodity.grade_id.grade_name != new_grade_name
        ):
            messages.error(request, "Commodity already exists!")
            return redirect('update_commodity', id)

        old_name = commodity.commodity_name
        old_grade = commodity.grade_id.grade_name
        old_shelf_life = commodity.shelf_life
        old_purchase_price = commodity.purchase_price
        old_selling_price = commodity.selling_price

        commodity.grade_id = models.Grade.objects.get(grade_name=new_grade_name)
        commodity.commodity_name = new_commodity_name
        commodity.shelf_life = new_shelf_life
        commodity.purchase_price = new_purchase_price
        commodity.selling_price = new_selling_price
        commodity.save()

        models.ActivityLog(
            user=request.user,
            action="Update Commodity",
            description=(
                f"Updated commodity ID {commodity.commodity_id}:\n "
                f"From: {old_name} (Grade: {old_grade}, Purchase: {old_purchase_price}, Selling: {old_selling_price})\n "
                f"To: {new_commodity_name} (Grade: {new_grade_name}, Purchase: {new_purchase_price}, Selling: {new_selling_price})\n"
            )
        ).save()

        messages.success(request, "Commodity has been successfully updated!")
        return redirect('read_commodity')

@login_required(login_url='login')
@role_required(['owner'])
def delete_commodity(request, id):
    commodity = models.Commodity.objects.get(commodity_id=id)
    name = commodity.commodity_name
    grade = commodity.grade_id.grade_name

    models.ActivityLog(
        user=request.user,
        action="Delete Commodity",
        description=(
            f"Deleted commodity: {name} (Grade: {grade})."
        )
    ).save()
    
    commodity.delete()
    messages.error(request, "Commodity has been deleted!")
    return redirect('read_commodity')

@login_required(login_url='login')
@role_required(['owner'])
def create_product(request):

    commodity_obj = models.Commodity.objects.filter(
        grade_id__grade_name="Processed"
    )

    if request.method == "GET":
        return render(request, "product/create_product.html", {"commodity_obj": commodity_obj})

    product_name = request.POST["product_name"]
    selling_price = request.POST["selling_price"]
    commodity_quantity = request.POST["commodity_quantity"]

    if models.Product.objects.filter(product_name=product_name).exists():
        messages.error(request, "Product name already exists!")
        return redirect("create_product")

    commodity_instance = models.Commodity.objects.get(
        commodity_id=request.POST["commodity_id"]
    )

    data = models.Product.objects.create(
        product_name=product_name,
        selling_price=selling_price,
        commodity_id=commodity_instance,
        commodity_quantity=commodity_quantity,
    )

    models.ActivityLog.objects.create(
        user=request.user,
        action="Add Product",
        description=f"Added new product: {data.product_name}, price {data.selling_price}."
    )

    messages.success(request, "Product has been successfully added!")
    return redirect("read_product")


@login_required(login_url='login')
@role_required(['owner', 'admin', 'production'])
def read_product(request):
    product_obj = models.Product.objects.all()
    if not product_obj.exists():
        messages.error(request, "No product data found!")

    return render(request, 'product/read_product.html', {
        'product_obj': product_obj
    })


@login_required(login_url='login')
@role_required(['owner'])
def update_product(request, id):
    try:
        product = models.Product.objects.get(product_id=id)
    except models.Product.DoesNotExist:
        messages.error(request, "Product not found!")
        return redirect("read_product")

    commodity_obj = models.Commodity.objects.filter(grade_id__grade_name="Processed")

    if request.method == "GET":
        return render(request, "product/update_product.html", {"product": product, "commodity_obj": commodity_obj})

    product_name = request.POST["product_name"]
    selling_price = request.POST["selling_price"]
    commodity_quantity = request.POST["commodity_quantity"]
    commodity_id = request.POST["commodity_id"]

    if models.Product.objects.filter(product_name=product_name).exclude(product_id=id).exists():
        messages.error(request, "Product name already exists!")
        return render(request, "product/update_product.html", {"product": product, "commodity_obj": commodity_obj,})

    try:
        commodity = models.Commodity.objects.get(commodity_id=commodity_id, grade_id__grade_name="Processed")
    except models.Commodity.DoesNotExist:
        messages.error(request, "Selected commodity is invalid!")
        return redirect("update_product", id=id)

    old_name = product.product_name
    old_price = product.selling_price
    old_qty = product.commodity_quantity
    old_commodity = product.commodity_id

    product.product_name = product_name
    product.selling_price = selling_price
    product.commodity_quantity = commodity_quantity
    product.commodity_id = commodity
    product.save()

    models.ActivityLog.objects.create(
        user=request.user,
        action="Update Product",
        description=(
            f"Updated product '{old_name}'. "
            f"Commodity: {old_commodity} → {commodity}. "
            f"Selling Price: {old_price} → {selling_price}. "
            f"Commodity Quantity: {old_qty} kg → {commodity_quantity} kg."
        )
    )

    messages.success(request, "Product has been successfully updated!")
    return redirect("read_product")


@login_required(login_url='login')
@role_required(['owner'])
def delete_product(request, id):
    product = models.Product.objects.get(product_id=id)
    name = product.product_name
    price = product.selling_price

    product.delete()

    models.ActivityLog(
        user=request.user,
        action="Delete Product",
        description=(
            f"Deleted product: {name}, price {price}."
        )
    ).save()

    messages.error(request, "Product has been deleted!")
    return redirect('read_product')

@login_required(login_url='login')
@role_required(['owner'])
def create_market(request):
    if request.method == 'GET':
        return render(request, 'market/create_market.html')
    else:
        market_name = request.POST['market_name']
        market_address = request.POST['market_address']
        phone_number = request.POST['phone_number']

        market_obj = models.Market.objects.filter(market_name=market_name)
        if market_obj.exists():
            messages.error(request, 'Market name already exists!')
        else:
            data = models.Market(
                market_name=market_name,
                market_address=market_address,
                phone_number=phone_number,
            )
            data.save()

            models.ActivityLog(
                user=request.user,
                action="Add Market",
                description=f"Added new market: {data.market_name}, located at {data.market_address}."
            ).save()
            messages.success(request, 'Market successfully added!')

        return redirect('read_market')

@login_required(login_url='login')
@role_required(['owner', 'admin'])
def read_market(request):
    market_obj = models.Market.objects.all()
    if not market_obj.exists():
        messages.error(request, "No market data found!")
    
    return render(request, 'market/read_market.html', {
        'market_obj': market_obj
    })

@login_required(login_url='login')
@role_required(['owner'])
def update_market(request, id):
    market = models.Market.objects.get(market_id=id)
    if request.method == 'GET':
        return render(request, 'market/update_market.html', {
            'market': market,
            'id': id
        })
    else:
        market_name = request.POST['market_name']
        market_address = request.POST['market_address']
        phone_number = request.POST['phone_number']

        existing = models.Market.objects.filter(market_name=market_name)
        if existing.exists() and market.market_name != market_name:
            messages.error(request, 'Market name already exists!')
            return redirect('update_market', id)

        old_name = market.market_name
        old_address = market.market_address

        market.market_name = market_name
        market.market_address = market_address
        market.phone_number = phone_number
        market.save()

        models.ActivityLog(
            user=request.user,
            action="Update Market",
            description=f"Updated market from '{old_name} - {old_address}' \n to '{market_name} - {market_address}'."
        ).save()

        messages.success(request, 'Market successfully updated!')
        return redirect('read_market')   

@login_required(login_url='login')
@role_required(['owner'])
def delete_market(request, id):
    market_obj = models.Market.objects.get(market_id=id)
    name = market_obj.market_name
    address = market_obj.market_address

    market_obj.delete()

    models.ActivityLog(
        user=request.user,
        action="Delete Market",
        description=f"Deleted market {name} located at {address}."
    ).save()

    messages.success(request, "Market successfully deleted!")
    return redirect('read_market')    


@login_required(login_url="login")
@role_required(["owner", "admin"])
def read_partner_harvest(request):
    harvest_qs = models.PartnerHarvestDetail.objects.select_related(
        "partner_harvest_id__partner_id",
        "commodity_id__grade_id",
    ).order_by("-partner_harvest_id__harvest_date")

    if not harvest_qs.exists():
        messages.error(request, "No Partner Harvest data found!")

    return render(request, "harvest/partner/read_partner_harvest.html", {
        "harvest_qs": harvest_qs,
    })


@login_required(login_url="login")
@role_required(["owner"])
def create_partner_harvest(request):
    all_partners = models.Partner.objects.filter(partner_status="Active")
    all_commodities = models.Commodity.objects.all()

    if request.method == "GET":
        return render(request, "harvest/partner/create_partner_harvest.html", {
            "all_partners": all_partners,
            "all_commodities": all_commodities,
        })
    else:
        partner_id = request.POST.get("partner_name") or request.POST.get("partner")
        harvest_date = request.POST.get("harvest_date")
        commodities = request.POST.getlist("commodity")
        quantities = request.POST.getlist("quantity")

        if not partner_id or not harvest_date:
            messages.error(request, "Partner and harvest date are required!")
            return redirect("create_partner_harvest")

        try:
            partner_obj = models.Partner.objects.get(partner_id=partner_id, partner_status="Active")
        except models.Partner.DoesNotExist:
            messages.error(request, "Selected partner is not active or does not exist!")
            return redirect("create_partner_harvest")

        harvest = models.PartnerHarvest(
            partner_id=partner_obj,
            harvest_date=harvest_date,
        )
        harvest.save()
        harvest.refresh_from_db()

        saved_details = []
        for commodity_id, quantity in zip(commodities, quantities):
            if not commodity_id or not quantity:
                continue

            try:
                commodity_obj = models.Commodity.objects.get(commodity_id=commodity_id)
            except models.Commodity.DoesNotExist:
                continue

            detail = models.PartnerHarvestDetail(
                partner_harvest_id=harvest,
                commodity_id=commodity_obj,
                quantity=quantity,
            )
            detail.save()
            saved_details.append(detail)

            models.InventoryBatch.objects.create(
                commodity_id=commodity_obj,
                harvest_date=harvest.harvest_date,
                expired_date=harvest.harvest_date + timedelta(days=commodity_obj.shelf_life),
                initial_quantity=quantity,
                remaining_quantity=quantity,
                source="Partner",
            )

        if not saved_details:
            harvest.delete()
            messages.error(request, "No valid Partner Harvest detail data was saved!")
            return redirect("create_partner_harvest")

        detail_summary = ", ".join(
            f"{detail.commodity_id} ({detail.quantity} kg)" for detail in saved_details
        )

        models.ActivityLog.objects.create(
            user=request.user,
            action="Add Partner Harvest",
            description=(
                f"Added partner harvest for {partner_obj.partner_name} on {harvest_date}: "
                f"{detail_summary}."
            )
        )

        messages.success(request, "Partner Harvest successfully added!")
        return redirect("read_partner_harvest")


@login_required(login_url="login")
@role_required(["owner", "admin"])
def update_partner_harvest(request, id):
    try:
        detail_obj = models.PartnerHarvestDetail.objects.select_related(
            "partner_harvest_id__partner_id",
            "commodity_id__grade_id",
        ).get(partner_harvest_detail_id=id)
    except models.PartnerHarvestDetail.DoesNotExist:
        messages.error(request, "Partner Harvest detail not found!")
        return redirect("read_partner_harvest")

    partners = models.Partner.objects.all()
    commodities = models.Commodity.objects.all()
    harvest_date = detail_obj.partner_harvest_id.harvest_date.strftime("%Y-%m-%d")

    if request.method == "GET":
        return render(request, "harvest/partner/update_partner_harvest.html", {
            "detail_obj": detail_obj,
            "partners": partners,
            "commodities": commodities,
            "harvest_date": harvest_date,
        })
    else:
        partner_id = request.POST.get("partner_name") or request.POST.get("partner")
        new_harvest_date = request.POST.get("harvest_date")
        commodity_id = request.POST.get("commodity")
        quantity = request.POST.get("quantity")

        if not partner_id or not new_harvest_date or not commodity_id or not quantity:
            messages.error(request, "All Partner Harvest fields are required!")
            return redirect("update_partner_harvest", id=id)

        try:
            partner_obj = models.Partner.objects.get(partner_id=partner_id)
            commodity_obj = models.Commodity.objects.get(commodity_id=commodity_id)
        except (models.Partner.DoesNotExist, models.Commodity.DoesNotExist):
            messages.error(request, "Selected partner or commodity is invalid!")
            return redirect("update_partner_harvest", id=id)

        old_partner = detail_obj.partner_harvest_id.partner_id.partner_name
        old_date = detail_obj.partner_harvest_id.harvest_date
        old_commodity = detail_obj.commodity_id
        old_quantity = detail_obj.quantity

        harvest = detail_obj.partner_harvest_id
        harvest.partner_id = partner_obj
        harvest.harvest_date = new_harvest_date
        harvest.save()

        detail_obj.commodity_id = commodity_obj
        detail_obj.quantity = quantity
        detail_obj.save()

        models.ActivityLog.objects.create(
            user=request.user,
            action="Update Partner Harvest",
            description=(
                f"Updated partner harvest detail ID {detail_obj.partner_harvest_detail_id}: "
                f"{old_partner}, {old_date}, {old_commodity}, {old_quantity} kg -> "
                f"{partner_obj.partner_name}, {new_harvest_date}, {commodity_obj}, {quantity} kg."
            )
        )

        messages.success(request, "Partner Harvest successfully updated!")
        return redirect("read_partner_harvest")


@login_required(login_url="login")
@role_required(["owner"])
def delete_partner_harvest(request, id):
    try:
        detail_obj = models.PartnerHarvestDetail.objects.select_related(
            "partner_harvest_id__partner_id",
            "commodity_id__grade_id",
        ).get(partner_harvest_detail_id=id)
    except models.PartnerHarvestDetail.DoesNotExist:
        messages.error(request, "Partner Harvest detail not found!")
        return redirect("read_partner_harvest")

    harvest = detail_obj.partner_harvest_id
    partner_name = harvest.partner_id.partner_name
    harvest_date = harvest.harvest_date
    commodity = detail_obj.commodity_id
    quantity = detail_obj.quantity

    models.ActivityLog.objects.create(
        user=request.user,
        action="Delete Partner Harvest",
        description=(
            f"Deleted partner harvest detail: {partner_name}, {harvest_date}, "
            f"{commodity}, {quantity} kg."
        )
    )

    detail_obj.delete()
    if not models.PartnerHarvestDetail.objects.filter(partner_harvest_id=harvest).exists():
        harvest.delete()

    messages.success(request, "Partner Harvest successfully deleted!")
    return redirect("read_partner_harvest")


@login_required(login_url="login")
@role_required(["owner", "admin", "inspection"])
def read_local_harvest(request):
    harvests = models.LocalHarvestDetail.objects.select_related(
        "local_harvest_id",
        "commodity_id__grade_id",
    ).order_by("-local_harvest_id__harvest_date")

    if not harvests.exists():
        messages.error(request, "No Local Harvest data found!")

    return render(request, "harvest/local/read_local_harvest.html", {
        "harvests": harvests,
    })


@login_required(login_url="login")
@role_required(["owner"])
def create_local_harvest(request):
    all_commodities = models.Commodity.objects.all()

    if request.method == "GET":
        return render(request, "harvest/local/create_local_harvest.html", {
            "all_commodities": all_commodities,
            "allcommodity": all_commodities,
        })
    else:
        harvest_date = request.POST.get("harvest_date")
        commodities = request.POST.getlist("commodity")
        quantities = request.POST.getlist("quantity")

        if not harvest_date:
            messages.error(request, "Harvest date is required!")
            return redirect("create_local_harvest")

        harvest = models.LocalHarvest(
            harvest_date=harvest_date,
        )
        harvest.save()
        harvest.refresh_from_db()

        saved_details = []
        for commodity_id, quantity in zip(commodities, quantities):
            if not commodity_id or not quantity:
                continue

            try:
                commodity_obj = models.Commodity.objects.get(commodity_id=commodity_id)
            except models.Commodity.DoesNotExist:
                continue

            detail = models.LocalHarvestDetail(
                local_harvest_id=harvest,
                commodity_id=commodity_obj,
                quantity=quantity,
            )
            detail.save()
            saved_details.append(detail)

            models.InventoryBatch.objects.create(
                commodity_id=commodity_obj,
                harvest_date=harvest.harvest_date,
                expired_date=harvest.harvest_date + timedelta(days=commodity_obj.shelf_life),
                initial_quantity=quantity,
                remaining_quantity=quantity,
                source="Local",
            )

        if not saved_details:
            harvest.delete()
            messages.error(request, "No valid Local Harvest detail data was saved!")
            return redirect("create_local_harvest")

        detail_summary = ", ".join(
            f"{detail.commodity_id} ({detail.quantity} kg)" for detail in saved_details
        )

        models.ActivityLog.objects.create(
            user=request.user,
            action="Add Local Harvest",
            description=f"Added local harvest on {harvest_date}: {detail_summary}."
        )

        messages.success(request, "Local Harvest successfully added!")
        return redirect("read_local_harvest")


@login_required(login_url="login")
@role_required(["owner", "admin"])
def update_local_harvest(request, id):
    try:
        detail_obj = models.LocalHarvestDetail.objects.select_related(
            "local_harvest_id",
            "commodity_id__grade_id",
        ).get(local_harvest_detail_id=id)
    except models.LocalHarvestDetail.DoesNotExist:
        messages.error(request, "Local Harvest detail not found!")
        return redirect("read_local_harvest")

    all_commodities = models.Commodity.objects.all()
    harvest_date = detail_obj.local_harvest_id.harvest_date.strftime("%Y-%m-%d")

    if request.method == "GET":
        return render(request, "harvest/local/update_local_harvest.html", {
            "detail_obj": detail_obj,
            "all_commodities": all_commodities,
            "harvest_date": harvest_date,
        })
    else:
        new_harvest_date = request.POST.get("harvest_date")
        commodity_id = request.POST.get("commodity")
        quantity = request.POST.get("quantity")

        if not new_harvest_date or not commodity_id or not quantity:
            messages.error(request, "All Local Harvest fields are required!")
            return redirect("update_local_harvest", id=id)

        try:
            commodity_obj = models.Commodity.objects.get(commodity_id=commodity_id)
        except models.Commodity.DoesNotExist:
            messages.error(request, "Selected commodity is invalid!")
            return redirect("update_local_harvest", id=id)

        old_date = detail_obj.local_harvest_id.harvest_date
        old_commodity = detail_obj.commodity_id
        old_quantity = detail_obj.quantity

        harvest = detail_obj.local_harvest_id
        harvest.harvest_date = new_harvest_date
        harvest.save()

        detail_obj.commodity_id = commodity_obj
        detail_obj.quantity = quantity
        detail_obj.save()

        models.ActivityLog.objects.create(
            user=request.user,
            action="Update Local Harvest",
            description=(
                f"Updated local harvest detail ID {detail_obj.local_harvest_detail_id}: "
                f"{old_date}, {old_commodity}, {old_quantity} kg -> "
                f"{new_harvest_date}, {commodity_obj}, {quantity} kg."
            )
        )

        messages.success(request, "Local Harvest successfully updated!")
        return redirect("read_local_harvest")


@login_required(login_url="login")
@role_required(["owner"])
def delete_local_harvest(request, id):
    try:
        detail_obj = models.LocalHarvestDetail.objects.select_related(
            "local_harvest_id",
            "commodity_id__grade_id",
        ).get(local_harvest_detail_id=id)
    except models.LocalHarvestDetail.DoesNotExist:
        messages.error(request, "Local Harvest detail not found!")
        return redirect("read_local_harvest")

    harvest = detail_obj.local_harvest_id
    harvest_date = harvest.harvest_date
    commodity = detail_obj.commodity_id
    quantity = detail_obj.quantity

    models.ActivityLog.objects.create(
        user=request.user,
        action="Delete Local Harvest",
        description=f"Deleted local harvest detail: {harvest_date}, {commodity}, {quantity} kg."
    )

    detail_obj.delete()
    if not models.LocalHarvestDetail.objects.filter(local_harvest_id=harvest).exists():
        harvest.delete()

    messages.success(request, "Local Harvest successfully deleted!")
    return redirect("read_local_harvest")

@login_required(login_url="login")
@role_required(["owner", "admin", "inspection"])
def read_inventory(request):
    inventory_qs = models.InventoryBatch.objects.select_related(
        "commodity_id__grade_id",
    ).order_by("expired_date")

    if not inventory_qs.exists():
        messages.error(request, "No Inventory data found!")

    return render(request, "inventory/read_inventory.html", {
        "inventory_qs": inventory_qs,
        "today": datetime.now().date(),
    })

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


