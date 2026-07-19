from django.urls import path
from . import views

urlpatterns = [
    path('',views.login_view, name='login'),
    path('performlogin',views.perform_login,name="performlogin"),
    path('performlogout',views.perform_logout,name="performlogout"),
    path('base', views.base,name='base'),
    # # CRUD PARTNER
    path('create_partner', views.create_partner,name='create_partner'),
    path('read_partner', views.read_partner,name='read_partner'),
    path('update_partner/<str:id>', views.update_partner,name='update_partner'),
    path('delete_partner/<str:id>', views.delete_partner,name='delete_partner'),
    # # CRUD SALE
    path('create_sale', views.create_sale,name='create_sale'),
    path('read_sale', views.read_sale,name='read_sale'),
    path('update_sale/<str:id>', views.update_sale,name='update_sale'),
    path('delete_sale/<str:id>', views.delete_sale,name='delete_sale'),
    # # CUD DETAIL SALE
    path('update_sale_product/<str:id>', views.update_sale_product,name='update_sale_product'),
    path('delete_sale_product/<str:id>', views.delete_sale_product,name='delete_sale_product'),
    path('update_sale_commodity/<str:id>', views.update_sale_commodity,name='update_sale_commodity'),
    path('delete_sale_commodity/<str:id>', views.delete_sale_commodity,name='delete_sale_commodity'),
    # CRUD PRODUCT
    path('create_product', views.create_product,name='create_product'),
    path('read_product', views.read_product,name='read_product'),
    path('update_product/<str:id>', views.update_product,name='update_product'),
    path('delete_product/<str:id>', views.delete_product,name='delete_product'),
    # # CRUD COMMODITY
    path('create_commodity', views.create_commodity,name='create_commodity'),
    path('read_commodity', views.read_commodity,name='read_commodity'),
    path('update_commodity/<str:id>', views.update_commodity,name='update_commodity'),
    path('delete_commodity/<str:id>', views.delete_commodity,name='delete_commodity'),
    # # CRUD GRADE
    path('create_grade', views.create_grade,name='create_grade'),
    path('read_grade',views.read_grade,name='read_grade'),
    path('update_grade/<str:id>', views.update_grade,name='update_grade'),
    path('delete_grade/<str:id>', views.delete_grade,name='delete_grade'),
    # # CRUD MARKET
    path('create_market', views.create_market,name='create_market'),
    path('read_market', views.read_market,name='read_market'),
    path('update_market/<str:id>', views.update_market,name='update_market'),
    path('delete_market/<str:id>', views.delete_market,name='delete_market'),
    # # CRUD TRANSACTION CATEGORY
    path('create_transactioncategory', views.create_transactioncategory,name='create_transactioncategory'),
    path('read_transactioncategory', views.read_transactioncategory,name='read_transactioncategory'),
    path('update_transactioncategory/<str:id>', views.update_transactioncategory,name='update_transactioncategory'),
    path('delete_transactioncategory/<str:id>', views.delete_transactioncategory,name='delete_transactioncategory'),
    # # CRUD TRANSACTION
    path('create_transaction', views.create_transaction,name='create_transaction'),
    path('read_transaction', views.read_transaction,name='read_transaction'),
    path('update_transaction/<str:id>', views.update_transaction,name='update_transaction'),
    path('delete_transaction/<str:id>', views.delete_transaction,name='delete_transaction'),
    # # CRUD PARTNER HARVEST
    path('create_partner_harvest', views.create_partner_harvest,name='create_partner_harvest'),
    path('read_partner_harvest', views.read_partner_harvest,name='read_partner_harvest'),
    path('update_partner_harvest/<str:id>', views.update_partner_harvest,name='update_partner_harvest'),
    path('delete_partner_harvest/<str:id>', views.delete_partner_harvest,name='delete_partner_harvest'),
    # # CRUD LOCAL HARVEST
    path('create_local_harvest', views.create_local_harvest,name='create_local_harvest'),
    path('read_local_harvest', views.read_local_harvest,name='read_local_harvest'),
    path('update_local_harvest/<str:id>', views.update_local_harvest,name='update_local_harvest'),
    path('delete_local_harvest/<str:id>', views.delete_local_harvest,name='delete_local_harvest'),
    # # READ INVENTORY
    path('read_inventory', views.read_inventory, name='read_inventory'),
    # # CRUD PRODUCTION
    path('read_production', views.read_production,name='read_production'),
    path('update_production/<str:id>', views.update_production,name='update_production'),
    # # REPORT
    path('sales_report', views.sales_report,name='sales_report'),
    path('harvest_report', views.harvest_report,name='harvest_report'),
    path('pnl_report', views.profit_and_loss_report,name='pnl_report'),
    path('profit_and_loss_pdf/<str:bulan>', views.profit_and_loss_pdf,name='profit_and_loss_pdf'),
    # # ADD
    path('total_commodities/', views.total_commodities, name='total_commodities'),
    # # Activity Log
    path('activity_logs/', views.activity_logs, name='activity_logs'),
    path('logs/delete/<int:id>/', views.delete_log, name='delete_log')
]
