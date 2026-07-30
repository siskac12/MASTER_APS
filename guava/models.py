from django.db import models
from django.contrib.auth.models import User

# Create your models here.

PARTNER_STATUS_CHOICES = [
    ("Pending", "Pending"),
    ("Active", "Active"),
    ("Rejected", "Rejected"),
    ("Inactive", "Inactive"),
]

class Partner(models.Model):
    partner_id = models.AutoField(primary_key=True)
    partner_name = models.CharField(max_length=100)
    partner_address = models.TextField(blank=True, null=True)
    partner_phone = models.PositiveBigIntegerField()
    start_date = models.DateField()
    contract_duration = models.PositiveIntegerField()
    land_area = models.PositiveIntegerField(null=True)
    partner_status = models.CharField(max_length=20, choices=PARTNER_STATUS_CHOICES, default="Pending")
    email = models.EmailField() 
    document = models.FileField() 
    inspection_notes = models.TextField(blank=True, null=True) 

    def __str__(self):
        return str(self.partner_name)


class Grade(models.Model):
    grade_id = models.AutoField(primary_key=True)
    grade_name = models.CharField(max_length=100)
    grade_description = models.TextField(blank=True, null=True)

    def __str__(self):
        return str(self.grade_name)


class Commodity(models.Model):
    commodity_id = models.AutoField(primary_key=True)
    commodity_name = models.CharField(max_length=100)
    grade_id = models.ForeignKey(Grade, on_delete=models.CASCADE)
    shelf_life = models.PositiveIntegerField()
    purchase_price = models.PositiveBigIntegerField()
    selling_price = models.PositiveBigIntegerField()

    def __str__(self):
        return f"{self.commodity_name} - {self.grade_id.grade_name}"


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=100)
    selling_price = models.PositiveIntegerField()
    production_cost = models.PositiveIntegerField(default=0)
    commodity_id = models.ForeignKey(Commodity, on_delete=models.CASCADE)
    commodity_quantity = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return str(self.product_name)


class PartnerHarvest(models.Model):
    partner_harvest_id = models.AutoField(primary_key=True)
    partner_id = models.ForeignKey(Partner, on_delete=models.CASCADE)
    harvest_date = models.DateField()

    def __str__(self):
        return str(self.partner_id.partner_name)


class PartnerHarvestDetail(models.Model):
    partner_harvest_detail_id = models.AutoField(primary_key=True)
    partner_harvest_id = models.ForeignKey(PartnerHarvest, on_delete=models.CASCADE)
    commodity_id = models.ForeignKey(Commodity, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return "{} - {}".format(self.partner_harvest_id)


class LocalHarvest(models.Model):
    local_harvest_id = models.AutoField(primary_key=True)
    harvest_date = models.DateField()

    def __str__(self):
        return str(self.local_harvest_id)


class LocalHarvestDetail(models.Model):
    local_harvest_detail_id = models.AutoField(primary_key=True)
    local_harvest_id = models.ForeignKey(LocalHarvest, on_delete=models.CASCADE)
    commodity_id = models.ForeignKey(Commodity, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return "{} - {}".format(self.local_harvest_id)


class Market(models.Model):
    market_id = models.AutoField(primary_key=True)
    market_name = models.CharField(max_length=100)
    market_address = models.TextField()
    phone_number = models.PositiveBigIntegerField()

    def __str__(self):
        return str(self.market_name)


class Sale(models.Model):
    sale_id = models.AutoField(primary_key=True)
    market_id = models.ForeignKey(Market, on_delete=models.CASCADE)
    date = models.DateField()

    def __str__(self):
        return str(self.market_id)

class SaleCommodity(models.Model):
    sale_commodity_id = models.AutoField(primary_key=True)
    sale_id = models.ForeignKey(Sale, on_delete=models.CASCADE)
    commodity_id = models.ForeignKey(Commodity, on_delete=models.CASCADE)
    grade_id = models.ForeignKey(Grade, on_delete=models.CASCADE)
    commodity_quantity = models.PositiveIntegerField()


class SaleProduct(models.Model):
    sale_product_id = models.AutoField(primary_key=True)
    sale_id = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_quantity = models.PositiveIntegerField()


class Production(models.Model):
    production_id = models.AutoField(primary_key=True)
    date = models.DateField()

    def __str__(self):
        return str(self.date)

PRODUCTION_STATUS_CHOICES = [
    ("Processing", "Processing"),
    ("Completed", "Completed"),
    ("Cancelled", "Cancelled"),
]

class ProductionDetail(models.Model):
    production_detail_id = models.AutoField(primary_key=True)
    production_id = models.ForeignKey(Production, on_delete=models.CASCADE)
    sale_product_id = models.ForeignKey(SaleProduct, on_delete=models.CASCADE, null=True)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    product_quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=PRODUCTION_STATUS_CHOICES, default="Processing")

    def __str__(self):
        return "{} - {}".format(self.production_id, self.product_id)


SOURCE_CHOICES = [
    ("Partner", "Partner"),
    ("Local", "Local"),
]

class InventoryBatch(models.Model):
    inventory_batch_id = models.AutoField(primary_key=True)
    commodity_id = models.ForeignKey(Commodity, on_delete=models.CASCADE)
    harvest_date = models.DateField()
    expired_date = models.DateField()
    initial_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    source_detail_id = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.commodity_id} ({self.remaining_quantity} kg)"

class InventoryUsage(models.Model):
    inventory_usage_id = models.AutoField(primary_key=True)
    inventory_batch_id = models.ForeignKey(InventoryBatch, on_delete=models.CASCADE)
    sale_commodity_id = models.ForeignKey(SaleCommodity, on_delete=models.CASCADE, null=True, blank=True)
    sale_product_id = models.ForeignKey(SaleProduct, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.inventory_batch_id} ({self.quantity} kg)"

CATEGORY_TYPE = [
    ("Income","Income"),
    ("Expense","Expense"),
]

class TransactionCategory(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=CATEGORY_TYPE)

    def __str__(self):
        return self.category_name
    

REFERENCE_TYPE = [
    ("Manual", "Manual"),
    ("SaleProduct", "Sale Product"),
    ("SaleCommodity", "Sale Commodity"),
    ("PartnerHarvest", "Partner Harvest"),
    ("Cost", "Cost"),
    ("Production", "Production")
]

class Transaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    category_id = models.ForeignKey(TransactionCategory, on_delete=models.CASCADE)
    date = models.DateField()
    description = models.CharField(max_length=200)
    amount = models.PositiveIntegerField()
    reference_type = models.CharField(max_length=30, choices=REFERENCE_TYPE)
    reference_id = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.reference_type} #{self.reference_id} - Rp{self.amount}"


class ActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
