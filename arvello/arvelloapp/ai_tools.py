from .models import Invoice, InvoiceProduct, Offer, OfferProduct, Product, Supplier, Expense, Company, Inventory, Client, Employee, Salary
from django.db.models import Q
from django.utils import timezone
from simple_history.utils import get_history_model_for_model


def filter_invoices_to_string(**criteria):
    """
    Filters invoices based on provided criteria and returns all matching invoice data as a formatted string.
    
    Supported criteria:
    - client_id: Filter by client ID
    - client_name: Filter by client name (partial match)
    - subject_id: Filter by subject (company) ID
    - is_paid: Filter by payment status (True/False)
    - due_date_from: Filter invoices with due date from this date (YYYY-MM-DD)
    - due_date_to: Filter invoices with due date to this date (YYYY-MM-DD)
    - date_from: Filter invoices created from this date (YYYY-MM-DD)
    - date_to: Filter invoices created to this date (YYYY-MM-DD)
    - number: Filter by invoice number (partial match)
    - product_id: Filter by product ID (invoices containing this product)
    - product_title: Filter by product title (partial match, invoices containing products with this title)
    - invoice_type: Filter by invoice type ('maloprodajni' for F1 retail, 'veleprodajni' for F2 wholesale)
    - payment_method: Filter by payment method ('cash', 'card', 'bank_transfer', 'other')
    """
    queryset = Invoice.objects.all()
    
    if 'client_id' in criteria:
        queryset = queryset.filter(client_id=criteria['client_id'])
    if 'client_name' in criteria:
        queryset = queryset.filter(client__clientName__icontains=criteria['client_name'])
    if 'subject_id' in criteria:
        queryset = queryset.filter(subject_id=criteria['subject_id'])
    if 'is_paid' in criteria:
        queryset = queryset.filter(is_paid=criteria['is_paid'])
    if 'due_date_from' in criteria:
        queryset = queryset.filter(dueDate__gte=criteria['due_date_from'])
    if 'due_date_to' in criteria:
        queryset = queryset.filter(dueDate__lte=criteria['due_date_to'])
    if 'date_from' in criteria:
        queryset = queryset.filter(date__gte=criteria['date_from'])
    if 'date_to' in criteria:
        queryset = queryset.filter(date__lte=criteria['date_to'])
    if 'number' in criteria:
        queryset = queryset.filter(number__icontains=criteria['number'])
    
    # Filter by product
    if 'product_id' in criteria:
        invoice_ids = InvoiceProduct.objects.filter(
            product_id=criteria['product_id']
        ).values_list('invoice_id', flat=True)
        queryset = queryset.filter(id__in=invoice_ids)
    if 'product_title' in criteria:
        invoice_ids = InvoiceProduct.objects.filter(
            product__title__icontains=criteria['product_title']
        ).values_list('invoice_id', flat=True)
        queryset = queryset.filter(id__in=invoice_ids)
    
    result = []
    for invoice in queryset:
        data = f"Invoice ID: {invoice.id}\n"
        data += f"Title: {invoice.title or 'N/A'}\n"
        data += f"Number: {invoice.number}\n"
        data += f"Date: {invoice.date}\n"
        data += f"Due Date: {invoice.dueDate}\n"
        data += f"Client: {invoice.client.clientName}\n"
        data += f"Subject: {invoice.subject.clientName}\n"
        data += f"Paid: {'Yes' if invoice.is_paid else 'No'}\n"
        data += f"Payment Date: {invoice.payment_date or 'N/A'}\n"
        data += f"Invoice Type: {invoice.get_invoice_type_display() if invoice.invoice_type else 'N/A'}\n"
        data += f"Payment Method: {invoice.get_payment_method_display() if invoice.payment_method else 'N/A'}\n"
        data += f"Notes: {invoice.notes or 'N/A'}\n"
        
        # Add products on this invoice
        invoice_products = InvoiceProduct.objects.filter(invoice=invoice).select_related('product')
        if invoice_products.exists():
            data += "Products:\n"
            for ip in invoice_products:
                product = ip.product
                data += f"  - {product.title}: Qty {ip.quantity}, Price {product.price} {product.currency}, "
                data += f"Discount {ip.discount or 0}%, Rabat {ip.rabat or 0}%, "
                data += f"Subtotal {ip.total()} {product.currency}\n"
        
        data += f"Pre-tax Amount: {invoice.pretax()}\n"
        data += f"Total with VAT: {invoice.price_with_vat()}\n"
        data += f"TAX: {invoice.tax()}\n"
        data += f"Currency: {invoice.curr()}\n"
        data += f"Reference: {invoice.reference()}\n"
        data += f"POZIV NA BROJ: {invoice.poziv_na_broj()}\n"
        data += "-----\n"
        result.append(data)
    
    return "\n".join(result) if result else "No invoices found matching the criteria."


def filter_offers_to_string(**criteria):
    """
    Filters offers based on provided criteria and returns all matching offer data as a formatted string.
    Offers are similar to invoices but represent price quotes/proposals sent to clients.
    Unlike invoices, offers don't require payment - they are proposals that may or may not be accepted.
    The due date (expiration date) on offers has no legal consequences if passed without payment.
    
    Supported criteria:
    - client_id: Filter by client ID
    - client_name: Filter by client name (partial match)
    - subject_id: Filter by subject (company) ID
    - due_date_from: Filter offers with expiration date from this date (YYYY-MM-DD)
    - due_date_to: Filter offers with expiration date to this date (YYYY-MM-DD)
    - date_from: Filter offers created from this date (YYYY-MM-DD)
    - date_to: Filter offers created to this date (YYYY-MM-DD)
    - number: Filter by offer number (partial match)
    - product_id: Filter by product ID (offers containing this product)
    - product_title: Filter by product title (partial match, offers containing products with this title)
    """
    queryset = Offer.objects.all()
    
    if 'client_id' in criteria:
        queryset = queryset.filter(client_id=criteria['client_id'])
    if 'client_name' in criteria:
        queryset = queryset.filter(client__clientName__icontains=criteria['client_name'])
    if 'subject_id' in criteria:
        queryset = queryset.filter(subject_id=criteria['subject_id'])
    if 'due_date_from' in criteria:
        queryset = queryset.filter(dueDate__gte=criteria['due_date_from'])
    if 'due_date_to' in criteria:
        queryset = queryset.filter(dueDate__lte=criteria['due_date_to'])
    if 'date_from' in criteria:
        queryset = queryset.filter(date__gte=criteria['date_from'])
    if 'date_to' in criteria:
        queryset = queryset.filter(date__lte=criteria['date_to'])
    if 'number' in criteria:
        queryset = queryset.filter(number__icontains=criteria['number'])
    
    # Filter by product
    if 'product_id' in criteria:
        offer_ids = OfferProduct.objects.filter(
            product_id=criteria['product_id']
        ).values_list('offer_id', flat=True)
        queryset = queryset.filter(id__in=offer_ids)
    if 'product_title' in criteria:
        offer_ids = OfferProduct.objects.filter(
            product__title__icontains=criteria['product_title']
        ).values_list('offer_id', flat=True)
        queryset = queryset.filter(id__in=offer_ids)
    
    result = []
    for offer in queryset:
        data = f"Offer ID: {offer.id}\n"
        data += f"Title: {offer.title or 'N/A'}\n"
        data += f"Number: {offer.number}\n"
        data += f"Date: {offer.date}\n"
        data += f"Expiration Date: {offer.dueDate}\n"
        data += f"Client: {offer.client.clientName}\n"
        data += f"Subject: {offer.subject.clientName}\n"
        data += f"Notes: {offer.notes or 'N/A'}\n"
        
        # Add products on this offer
        offer_products = OfferProduct.objects.filter(offer=offer).select_related('product')
        if offer_products.exists():
            data += "Products:\n"
            for op in offer_products:
                product = op.product
                data += f"  - {product.title}: Qty {op.quantity}, Price {product.price} {product.currency}, "
                data += f"Discount {op.discount or 0}%, Rabat {op.rabat or 0}%, "
                data += f"Subtotal {op.total()} {product.currency}\n"
        
        data += f"Pre-tax Amount: {offer.pretax()}\n"
        data += f"Total with VAT: {offer.price_with_vat()}\n"
        data += f"TAX: {offer.tax()}\n"
        data += f"Currency: {offer.curr()}\n"
        data += f"Reference: {offer.reference()}\n"
        data += f"POZIV NA BROJ: {offer.poziv_na_broj()}\n"
        data += "-----\n"
        result.append(data)
    
    return "\n".join(result) if result else "No offers found matching the criteria."


def get_suppliers_to_string():
    """
    Returns all suppliers data as a formatted string.
    No filtering needed - returns all suppliers.
    """
    queryset = Supplier.objects.all().order_by('supplierName')
    
    result = []
    for supplier in queryset:
        data = f"Supplier ID: {supplier.id}\n"
        data += f"Name: {supplier.supplierName}\n"
        data += f"Address: {supplier.addressLine1}\n"
        data += f"Town: {supplier.town}\n"
        data += f"Province: {supplier.province}\n"
        data += f"Postal Code: {supplier.postalCode}\n"
        data += f"Phone: {supplier.phoneNumber or 'N/A'}\n"
        data += f"Email: {supplier.emailAddress or 'N/A'}\n"
        data += f"Business Type: {supplier.businessType}\n"
        data += f"OIB: {supplier.OIB or 'N/A'}\n"
        data += f"IBAN: {supplier.IBAN or 'N/A'}\n"
        data += f"Notes: {supplier.notes or 'N/A'}\n"
        data += f"Date Created: {supplier.date_created}\n"
        data += "-----\n"
        result.append(data)
    
    return "\n".join(result) if result else "No suppliers found."


def get_expenses_to_string():
    """
    Returns all expenses data as a formatted string.
    No filtering needed - returns all expenses.
    """
    queryset = Expense.objects.all().order_by('-date')
    
    result = []
    for expense in queryset:
        data = f"Expense ID: {expense.id}\n"
        data += f"Title: {expense.title}\n"
        data += f"Amount: {expense.amount} {expense.currency}\n"
        data += f"Date: {expense.date}\n"
        data += f"Category: {expense.get_category_display()}\n"
        data += f"Description: {expense.description or 'N/A'}\n"
        data += f"Subject: {expense.subject.clientName}\n"
        data += f"Supplier: {expense.supplier.supplierName if expense.supplier else 'N/A'}\n"
        data += f"Invoice Number: {expense.invoice_number or 'N/A'}\n"
        data += f"Invoice Date: {expense.invoice_date or 'N/A'}\n"
        data += f"Pre-tax Amount: {expense.pretax_amount}\n"
        data += f"Tax Base 0%: {expense.tax_base_0}\n"
        data += f"Tax Base 5%: {expense.tax_base_5}\n"
        data += f"Tax Base 13%: {expense.tax_base_13}\n"
        data += f"Tax Base 25%: {expense.tax_base_25}\n"
        data += f"Total Tax Deductible: {expense.total_tax_deductible()}\n"
        data += f"Total Tax Non-deductible: {expense.total_tax_nondeductible()}\n"
        data += f"Date Created: {expense.date_created}\n"
        data += "-----\n"
        result.append(data)
    
    return "\n".join(result) if result else "No expenses found."


def get_subjects_to_string():
    """
    Returns all subjects (companies) data as a formatted string.
    No filtering needed - returns all companies/subjects.
    """
    queryset = Company.objects.all().order_by('clientName')
    
    result = []
    for company in queryset:
        data = f"Company ID: {company.id}\n"
        data += f"Name: {company.clientName}\n"
        data += f"Address: {company.addressLine1}\n"
        data += f"Town: {company.town}\n"
        data += f"Province: {company.province}\n"
        data += f"Postal Code: {company.postalCode}\n"
        data += f"Phone: {company.phoneNumber or 'N/A'}\n"
        data += f"Email: {company.emailAddress or 'N/A'}\n"
        data += f"Client Type: {company.clientType}\n"
        data += f"OIB: {company.OIB or 'N/A'}\n"
        data += f"VAT System: {'Yes' if company.SustavPDVa else 'No'}\n"
        data += f"IBAN: {company.IBAN or 'N/A'}\n"
        data += f"Client Unique ID: {company.clientUniqueId}\n"
        data += f"Date Created: {company.date_created}\n"
        data += "-----\n"
        result.append(data)
    
    return "\n".join(result) if result else "No companies/subjects found."


def get_inventory_to_string():
    """
    Returns all inventory items data as a formatted string.
    No filtering needed - returns all inventory items.
    """
    queryset = Inventory.objects.all().order_by('title')
    
    result = []
    for item in queryset:
        data = f"Inventory ID: {item.id}\n"
        data += f"Title: {item.title or 'N/A'}\n"
        data += f"Quantity: {item.quantity or 0}\n"
        data += f"Subject: {item.subject.clientName if item.subject else 'N/A'}\n"
        data += f"Date Created: {item.date_created}\n"
        data += f"Last Updated: {item.last_updated}\n"
        data += "-----\n"
        result.append(data)
    
    return "\n".join(result) if result else "No inventory items found."


def filter_clients_to_string(**criteria):
    """
    Filters clients based on provided criteria and returns all matching client data as a formatted string.
    
    Supported criteria:
    - name: Filter by client name (partial match)
    - province: Filter by province/county (partial match)
    """
    queryset = Client.objects.all()
    
    if 'name' in criteria:
        queryset = queryset.filter(clientName__icontains=criteria['name'])
    if 'province' in criteria:
        queryset = queryset.filter(province__icontains=criteria['province'])
    
    result = []
    for client in queryset:
        data = f"Client ID: {client.id}\n"
        data += f"Name: {client.clientName}\n"
        data += f"Address: {client.addressLine1}\n"
        data += f"Province: {client.province}\n"
        data += f"Postal Code: {client.postalCode}\n"
        data += f"Phone: {client.phoneNumber or 'N/A'}\n"
        data += f"Email: {client.emailAddress or 'N/A'}\n"
        data += f"Client Type: {client.clientType}\n"
        data += f"OIB: {client.OIB or 'N/A'}\n"
        data += f"VAT ID: {client.VATID}\n"
        data += f"VAT System: {'Yes' if client.SustavPDVa else 'No'}\n"
        data += f"IBAN: {client.IBAN or 'N/A'}\n"
        data += f"Client Unique ID: {client.clientUniqueId}\n"
        data += f"Date Created: {client.date_created}\n"
        data += "-----\n"
        result.append(data)
    
    return "\n".join(result) if result else "No clients found matching the criteria."


def filter_products_to_string(**criteria):
    """
    Filters products based on provided criteria and returns all matching product data as a formatted string.
    
    Supported criteria:
    - title: Filter by product title (partial match)
    - price_min: Filter products with price >= this value
    - price_max: Filter products with price <= this value
    - currency: Filter by currency (€, $, £)
    """
    queryset = Product.objects.all()
    
    if 'title' in criteria:
        # Case-insensitive search that works with Croatian characters (SQLite doesn't handle Unicode case folding)
        search_term = criteria['title'].lower()
        queryset = [p for p in queryset if search_term in p.title.lower()]
    # If title filter was applied, queryset is now a list - convert remaining filters to list comprehension
    if isinstance(queryset, list):
        if 'price_min' in criteria:
            queryset = [p for p in queryset if p.price >= criteria['price_min']]
        if 'price_max' in criteria:
            queryset = [p for p in queryset if p.price <= criteria['price_max']]
        if 'currency' in criteria:
            queryset = [p for p in queryset if p.currency == criteria['currency']]
    else:
        if 'price_min' in criteria:
            queryset = queryset.filter(price__gte=criteria['price_min'])
        if 'price_max' in criteria:
            queryset = queryset.filter(price__lte=criteria['price_max'])
        if 'currency' in criteria:
            queryset = queryset.filter(currency=criteria['currency'])
    
    result = []
    for product in queryset:
        data = f"Product ID: {product.id}\n"
        data += f"Title: {product.title}\n"
        data += f"Description: {product.description or 'N/A'}\n"
        data += f"Price: {product.price} {product.currency}\n"
        data += f"Price with VAT: {product.price_with_vat()} {product.currency}\n"
        data += f"Tax Percent: {product.taxPercent}%\n"
        data += f"Barcode ID: {product.barid}\n"
        data += f"Date Created: {product.date_created}\n"
        data += f"Last Updated: {product.last_updated}\n"
        data += "-----\n"
        result.append(data)
    
    return "\n".join(result) if result else "No products found matching the criteria."


def get_employees_to_string():
    """
    Returns all employees data as a formatted string.
    No filtering needed - returns all employees.
    """
    queryset = Employee.objects.all().order_by('last_name', 'first_name')
    
    result = []
    for employee in queryset:
        data = f"Employee ID: {employee.id}\n"
        data += f"Full Name: {employee.get_full_name()}\n"
        data += f"First Name: {employee.first_name}\n"
        data += f"Last Name: {employee.last_name}\n"
        data += f"Date of Birth: {employee.date_of_birth}\n"
        data += f"OIB: {employee.oib}\n"
        data += f"Email: {employee.email or 'N/A'}\n"
        data += f"Phone: {employee.phone or 'N/A'}\n"
        data += f"Address: {employee.address}\n"
        data += f"City: {employee.city}\n"
        data += f"Postal Code: {employee.postal_code}\n"
        data += f"Company: {employee.company.clientName}\n"
        data += f"Job Title: {employee.job_title}\n"
        data += f"Employment Type: {employee.get_employment_type_display()}\n"
        data += f"Date of Employment: {employee.date_of_employment}\n"
        data += f"Hourly Rate: {employee.hourly_rate} EUR\n"
        data += f"Tax Deduction Coefficient: {employee.tax_deduction_coefficient}\n"
        data += f"Work Experience Percentage: {employee.work_experience_percentage}%\n"
        data += f"Annual Vacation Days: {employee.annual_vacation_days}\n"
        data += f"Pension Pillar: {employee.get_pension_pillar_display()}\n"
        data += f"Pension Pillar 3 (Voluntary): {'Yes' if employee.pension_pillar_3 else 'No'}\n"
        data += f"IBAN: {employee.iban}\n"
        data += f"Active: {'Yes' if employee.is_active else 'No'}\n"
        data += f"Date Created: {employee.date_created}\n"
        data += f"Last Updated: {employee.last_updated}\n"
        data += "-----\n"
        result.append(data)
    
    return "\n".join(result) if result else "No employees found."


def get_salaries_to_string():
    """
    Returns all salaries data as a formatted string.
    No filtering needed - returns all salaries ordered by most recent first.
    """
    queryset = Salary.objects.all().select_related('employee', 'employee__company').order_by('-period_year', '-period_month')
    
    result = []
    for salary in queryset:
        data = f"Salary ID: {salary.id}\n"
        data += f"Employee: {salary.employee.get_full_name()}\n"
        data += f"Company: {salary.employee.company.clientName}\n"
        data += f"Period: {salary.period_month}/{salary.period_year}\n"
        data += f"Status: {salary.get_status_display()}\n"
        data += f"Regular Hours: {salary.regular_hours}\n"
        data += f"Vacation Days: {salary.vacation_days}\n"
        data += f"Vacation Hours: {salary.vacation_hours}\n"
        data += f"Overtime Hours: {salary.overtime_hours}\n"
        data += f"Sick Leave Hours: {salary.sick_leave_hours}\n"
        data += f"Regular Amount: {salary.regular_amount} EUR\n"
        data += f"Vacation Amount: {salary.vacation_amount} EUR\n"
        data += f"Overtime Amount: {salary.overtime_amount} EUR\n"
        data += f"Sick Leave Amount: {salary.sick_leave_amount} EUR\n"
        data += f"Experience Bonus: {salary.experience_bonus_amount} EUR\n"
        data += f"Bonus/Stimulation: {salary.bonus or 0} EUR\n"
        data += f"Gross Salary: {salary.gross_salary} EUR\n"
        data += f"Pension Pillar 1 (15%): {salary.pension_pillar_1} EUR\n"
        data += f"Pension Pillar 2 (5%): {salary.pension_pillar_2} EUR\n"
        data += f"Health Insurance (16.5%): {salary.health_insurance} EUR\n"
        data += f"Total Contributions: {salary.total_contributions} EUR\n"
        data += f"Tax Deduction: {salary.tax_deduction} EUR\n"
        data += f"Income Tax Base: {salary.income_tax_base} EUR\n"
        data += f"Income Tax: {salary.income_tax} EUR\n"
        data += f"Net Salary: {salary.net_salary} EUR\n"
        
        # Non-taxable payments
        if salary.non_taxable_payments:
            data += "Non-taxable Payments:\n"
            for payment_type, amount in salary.non_taxable_payments.items():
                data += f"  - {payment_type}: {amount} EUR\n"
        
        data += f"JOPPD Status: {'Reported' if salary.joppd_status else 'Not Reported'}\n"
        data += f"JOPPD Reference: {salary.joppd_reference or 'N/A'}\n"
        data += f"Payment Date: {salary.payment_date or 'N/A'}\n"
        data += f"Is Locked: {'Yes' if salary.is_locked else 'No'}\n"
        data += f"Notes: {salary.notes or 'N/A'}\n"
        data += f"Created At: {salary.created_at}\n"
        data += f"Updated At: {salary.updated_at}\n"
        data += "-----\n"
        result.append(data)
    
    return "\n".join(result) if result else "No salaries found."


def filter_change_history_to_string(**criteria):
    """
    Filters change history records based on provided criteria and returns them as a formatted string.
    
    Supported criteria:
    - model_name: Name of the model to get history for (e.g., 'Invoice', 'Client', 'Product', 'Expense', 'Supplier', 'Company', 'Inventory')
                  If not provided, returns history from ALL models.
    - date_from: Filter history from this date (YYYY-MM-DD)
    - date_to: Filter history to this date (YYYY-MM-DD)
    - object_id: Filter by specific object ID
    """
    from django.apps import apps
    
    # Map model names to their classes
    model_mapping = {
        'invoice': Invoice,
        'client': Client,
        'product': Product,
        'expense': Expense,
        'supplier': Supplier,
        'company': Company,
        'subject': Company,
        'inventory': Inventory,
        'employee': Employee,
        'salary': Salary,
    }
    
    model_name = criteria.get('model_name', '') or ''
    model_name = model_name.lower() if model_name else ''
    
    # Determine which models to query
    if model_name and model_name in model_mapping:
        models_to_query = {model_name: model_mapping[model_name]}
    elif model_name and model_name not in model_mapping:
        return f"Unknown model: {model_name}. Available models: Invoice, Client, Product, Expense, Supplier, Company, Inventory, Employee, Salary"
    else:
        # No model specified - query all models
        models_to_query = {
            'invoice': Invoice,
            'client': Client,
            'product': Product,
            'expense': Expense,
            'supplier': Supplier,
            'company': Company,
            'inventory': Inventory,
            'employee': Employee,
            'salary': Salary,
        }
    
    result = []
    total_records = 0
    max_per_model = 20 if len(models_to_query) > 1 else 100  # Limit per model when querying all
    
    for name, model_class in models_to_query.items():
        try:
            history_model = get_history_model_for_model(model_class)
            queryset = history_model.objects.all().order_by('-history_date')
            
            # Apply date filters
            if 'date_from' in criteria and criteria['date_from']:
                queryset = queryset.filter(history_date__date__gte=criteria['date_from'])
            if 'date_to' in criteria and criteria['date_to']:
                queryset = queryset.filter(history_date__date__lte=criteria['date_to'])
            if 'object_id' in criteria and criteria['object_id'] is not None:
                queryset = queryset.filter(id=criteria['object_id'])
            
            # Limit results
            queryset = queryset[:max_per_model]
            
            for record in queryset:
                total_records += 1
                data = f"Model: {name.capitalize()}\n"
                data += f"History ID: {record.history_id}\n"
                data += f"Object ID: {record.id}\n"
                data += f"Change Type: {record.history_type}\n"
                data += f"Change Date: {record.history_date}\n"
                data += f"Changed By: {record.history_user.username if record.history_user else 'System'}\n"
                
                # Add key identifying info based on model
                if hasattr(record, 'clientName'):
                    data += f"Name: {record.clientName}\n"
                elif hasattr(record, 'supplierName'):
                    data += f"Name: {record.supplierName}\n"
                elif hasattr(record, 'title'):
                    data += f"Title: {record.title}\n"
                elif hasattr(record, 'number'):
                    data += f"Number: {record.number}\n"
                
                data += "-----\n"
                result.append(data)
        except Exception as e:
            # Skip models that fail (e.g., no history table)
            continue
    
    if result:
        header = f"Found {total_records} change history records:\n\n"
        return header + "\n".join(result)
    else:
        return "No change history found matching the criteria."


# =============================================================================
# ACTION PROPOSAL FUNCTIONS
# These functions don't execute changes - they return structured action proposals
# that require user confirmation before being executed.
# =============================================================================

def propose_inventory_add(title=None, quantity=None, subject_name=None, subject_id=None):
    """
    Proposes adding a new inventory item. Does NOT execute the change.
    Returns an action proposal that requires user confirmation.
    
    Parameters (all required except one of subject_name/subject_id):
    - title: Name/title of the inventory item to add (REQUIRED)
    - quantity: Quantity to add (REQUIRED)
    - subject_name: Name of the subject/company (partial match) - provide this OR subject_id
    - subject_id: ID of the subject/company - provide this OR subject_name
    """
    import json
    
    # Validate required fields
    if not title:
        return json.dumps({
            "status": "error",
            "message": "Naziv stavke (title) je obavezan parametar."
        })
    
    if quantity is None:
        return json.dumps({
            "status": "error",
            "message": "Količina (quantity) je obavezan parametar."
        })
    
    if not subject_name and not subject_id:
        return json.dumps({
            "status": "error",
            "message": "Potrebno je navesti subjekt - subject_name ili subject_id."
        })
    
    # Find the subject
    if subject_id:
        try:
            subject = Company.objects.get(id=subject_id)
        except Company.DoesNotExist:
            return json.dumps({
                "status": "error",
                "message": f"Subjekt s ID-em {subject_id} nije pronađen."
            })
    elif subject_name:
        subjects = Company.objects.filter(clientName__icontains=subject_name)
        if not subjects.exists():
            return json.dumps({
                "status": "error",
                "message": f"Subjekt s imenom '{subject_name}' nije pronađen."
            })
        if subjects.count() > 1:
            names = [s.clientName for s in subjects[:5]]
            return json.dumps({
                "status": "error",
                "message": f"Pronađeno više subjekata s imenom '{subject_name}': {', '.join(names)}. Molimo budite precizniji."
            })
        subject = subjects.first()
    return json.dumps({
        "status": "action_required",
        "action_type": "inventory_add",
        "action_data": {
            "title": title,
            "quantity": quantity,
            "subject_id": subject.id,
            "subject_name": subject.clientName
        },
        "display_message": f"Dodaj stavku u inventar - Naziv: '{title}', Količina: {quantity}, Subjekt: {subject.clientName}"
    })


def propose_inventory_remove(item_title=None, item_id=None):
    """
    Proposes removing an inventory item. Does NOT execute the change.
    Returns an action proposal that requires user confirmation.
    
    Parameters (at least one is REQUIRED):
    - item_title: Title of the item to remove (partial match) - provide this OR item_id
    - item_id: ID of the item to remove - provide this OR item_title
    """
    import json
    
    # Validate at least one identifier is provided
    if not item_title and not item_id:
        return json.dumps({
            "status": "error",
            "message": "Potrebno je navesti item_title ili item_id stavke koju želite ukloniti."
        })
    
    if item_id:
        try:
            item = Inventory.objects.get(id=item_id)
        except Inventory.DoesNotExist:
            return json.dumps({
                "status": "error",
                "message": f"Stavka inventara s ID-em {item_id} nije pronađena."
            })
    elif item_title:
        items = Inventory.objects.filter(title__icontains=item_title)
        if not items.exists():
            return json.dumps({
                "status": "error",
                "message": f"Stavka inventara s nazivom '{item_title}' nije pronađena."
            })
        if items.count() > 1:
            titles = [i.title for i in items[:5]]
            return json.dumps({
                "status": "error",
                "message": f"Pronađeno više stavki s nazivom '{item_title}': {', '.join(titles)}. Molimo budite precizniji."
            })
        item = items.first()
    
    return json.dumps({
        "status": "action_required",
        "action_type": "inventory_remove",
        "action_data": {
            "item_id": item.id,
            "title": item.title,
            "quantity": item.quantity,
            "subject_name": item.subject.clientName if item.subject else "N/A"
        },
        "display_message": f"Ukloni stavku iz inventara - Naziv: '{item.title}', Trenutna količina: {item.quantity}, Subjekt: {item.subject.clientName if item.subject else 'N/A'}"
    })


def propose_inventory_update(item_title=None, item_id=None, new_title=None, new_quantity=None):
    """
    Proposes updating an inventory item. Does NOT execute the change.
    Returns an action proposal that requires user confirmation.
    
    Parameters:
    - item_title: Title of the item to update (partial match) - provide this OR item_id (one is REQUIRED)
    - item_id: ID of the item to update - provide this OR item_title (one is REQUIRED)
    - new_title: New title for the item - at least one of new_title or new_quantity is REQUIRED
    - new_quantity: New quantity for the item - at least one of new_title or new_quantity is REQUIRED
    """
    import json
    
    # Validate item identifier is provided
    if not item_title and not item_id:
        return json.dumps({
            "status": "error",
            "message": "Potrebno je navesti item_title ili item_id stavke koju želite promijeniti."
        })
    
    # Validate at least one change is requested
    if new_title is None and new_quantity is None:
        return json.dumps({
            "status": "error",
            "message": "Potrebno je navesti barem jednu promjenu - new_title ili new_quantity."
        })
    
    # Find the item
    if item_id:
        try:
            item = Inventory.objects.get(id=item_id)
        except Inventory.DoesNotExist:
            return json.dumps({
                "status": "error",
                "message": f"Stavka inventara s ID-em {item_id} nije pronađena."
            })
    elif item_title:
        items = Inventory.objects.filter(title__icontains=item_title)
        if not items.exists():
            return json.dumps({
                "status": "error",
                "message": f"Stavka inventara s nazivom '{item_title}' nije pronađena."
            })
        if items.count() > 1:
            titles = [i.title for i in items[:5]]
            return json.dumps({
                "status": "error",
                "message": f"Pronađeno više stavki s nazivom '{item_title}': {', '.join(titles)}. Molimo budite precizniji."
            })
        item = items.first()
    
    # Build changes description
    changes = []
    action_data = {"item_id": item.id, "current_title": item.title}
    
    if new_title and new_title != item.title:
        changes.append(f"naziv s '{item.title}' na '{new_title}'")
        action_data["new_title"] = new_title
        action_data["old_title"] = item.title
    
    if new_quantity is not None:
        try:
            new_qty = float(new_quantity)
            if new_qty != item.quantity:
                changes.append(f"količinu s {item.quantity} na {new_qty}")
                action_data["new_quantity"] = new_qty
                action_data["old_quantity"] = item.quantity
        except (ValueError, TypeError):
            return json.dumps({
                "status": "error",
                "message": f"Neispravna količina: {new_quantity}"
            })
    
    # Check if any actual changes were detected (values might be same as current)
    if not changes:
        return json.dumps({
            "status": "error",
            "message": "Navedene vrijednosti su iste kao trenutne. Nema promjena za napraviti."
        })
    
    return json.dumps({
        "status": "action_required",
        "action_type": "inventory_update",
        "action_data": action_data,
        "display_message": f"Promijeni stavku inventara - Trenutni naziv: '{item.title}', Nova količina: {new_quantity if new_quantity is not None else 'bez promjene'}, Novi naziv: '{new_title if new_title else 'bez promjene'}', Subjekt: {item.subject.clientName if item.subject else 'N/A'}"
    })


def propose_invoice_add(number=None, client_name=None, client_id=None, subject_name=None, subject_id=None,
                        date=None, due_date=None, title=None, notes=None, products=None,
                        invoice_type=None, payment_method=None):
    """
    Proposes creating a new invoice. Does NOT execute the change.
    Returns an action proposal that requires user confirmation.
    
    Parameters:
    - number: (REQUIRED) Broj računa - unique identifier for the invoice. Common Croatian practice is to use 
              format like "1/1/1" (broj/poslovni prostor/naplatni uređaj) or date-based like 
              "2026-001" (year-sequential). Check existing invoices with filter_invoices_to_string 
              to follow the established numbering convention used by this business.
    - client_name: Ime klijenta (djelomično podudaranje) - provide this OR client_id (one is REQUIRED)
    - client_id: ID klijenta - provide this OR client_name (one is REQUIRED)
    - subject_name: Naziv subjekta/tvrtke izdavatelja (djelomično podudaranje) - provide this OR subject_id (one is REQUIRED)
    - subject_id: ID subjekta/tvrtke izdavatelja - provide this OR subject_name (one is REQUIRED)
    - date: Datum računa u formatu YYYY-MM-DD - the invoice date (defaults to today if not provided)
    - due_date: (REQUIRED) Datum dospijeća u formatu YYYY-MM-DD - when payment is due (typically 15-30 days after date)
    - title: (REQUIRED) Naslov računa - brief description/title for the invoice
    - notes: Napomene (opcionalno) - additional notes to appear on the invoice
    - products: (REQUIRED) Lista proizvoda s količinama u formatu [{"product_name": "Naziv", "quantity": 1, "discount": 0, "rabat": 0}, ...]
                Svaki proizvod mora imati product_name i quantity. Polja discount i rabat su opcionalna.
                Koristi filter_products_to_string da pronađeš dostupne proizvode prije kreiranja računa.
    - invoice_type: (REQUIRED) Tip računa - 'maloprodajni' za F1 maloprodaju (fizičke osobe) ili 
                    'veleprodajni' za F2 veleprodaju (pravne osobe).
    - payment_method: (REQUIRED) Način plaćanja - 'cash' (gotovina), 'card' (kartica), 
                      'bank_transfer' (transakcijski račun), 'other' (ostalo).
    """
    import json
    from datetime import datetime, timedelta
    
    # Validate required fields
    if not number:
        return json.dumps({
            "status": "error",
            "message": "Broj računa (number) je obavezan parametar."
        })
    
    if not title:
        return json.dumps({
            "status": "error",
            "message": "Naslov računa (title) je obavezan parametar."
        })
    
    if not due_date:
        return json.dumps({
            "status": "error",
            "message": "Datum dospijeća (due_date) je obavezan parametar u formatu YYYY-MM-DD."
        })
    
    if not client_name and not client_id:
        return json.dumps({
            "status": "error",
            "message": "Potrebno je navesti klijenta - client_name ili client_id."
        })
    
    if not subject_name and not subject_id:
        return json.dumps({
            "status": "error",
            "message": "Potrebno je navesti subjekt - subject_name ili subject_id."
        })
    
    if not products:
        return json.dumps({
            "status": "error",
            "message": "Lista proizvoda (products) je obavezna. Koristi filter_products_to_string za pregled dostupnih proizvoda."
        })
    
    # Find client
    client = None
    if client_id:
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return json.dumps({
                "status": "error",
                "message": f"Klijent s ID-em {client_id} nije pronađen."
            })
    elif client_name:
        clients = Client.objects.filter(clientName__icontains=client_name)
        if clients.count() == 0:
            return json.dumps({
                "status": "error",
                "message": f"Klijent s imenom '{client_name}' nije pronađen."
            })
        elif clients.count() > 1:
            names = ", ".join([c.clientName for c in clients[:5]])
            return json.dumps({
                "status": "error",
                "message": f"Pronađeno više klijenata s imenom '{client_name}': {names}. Molimo budite precizniji."
            })
        client = clients.first()
    
    # Find subject (company)
    subject = None
    if subject_id:
        try:
            subject = Company.objects.get(id=subject_id)
        except Company.DoesNotExist:
            return json.dumps({
                "status": "error",
                "message": f"Subjekt s ID-em {subject_id} nije pronađen."
            })
    elif subject_name:
        subjects = Company.objects.filter(clientName__icontains=subject_name)
        if subjects.count() == 0:
            return json.dumps({
                "status": "error",
                "message": f"Subjekt s nazivom '{subject_name}' nije pronađen."
            })
        elif subjects.count() > 1:
            names = ", ".join([s.clientName for s in subjects[:5]])
            return json.dumps({
                "status": "error",
                "message": f"Pronađeno više subjekata s nazivom '{subject_name}': {names}. Molimo budite precizniji."
            })
        subject = subjects.first()
    
    # Parse and validate products
    product_list = []
    if products:
        for prod in products:
            product_name = prod.get('product_name') or prod.get('name') or prod.get('title')
            if not product_name:
                continue
            
            found_products = Product.objects.filter(title__icontains=product_name)
            if found_products.count() == 0:
                return json.dumps({
                    "status": "error",
                    "message": f"Proizvod '{product_name}' nije pronađen. Koristi filter_products_to_string za pregled dostupnih proizvoda."
                })
            elif found_products.count() > 1:
                names = ", ".join([p.title for p in found_products[:5]])
                return json.dumps({
                    "status": "error",
                    "message": f"Pronađeno više proizvoda s nazivom '{product_name}': {names}. Molimo budite precizniji."
                })
            
            product = found_products.first()
            # Validate quantity is provided for each product
            qty = prod.get('quantity')
            if qty is None:
                return json.dumps({
                    "status": "error",
                    "message": f"Količina (quantity) je obavezna za proizvod '{product_name}'."
                })
            
            product_list.append({
                "product_id": product.id,
                "product_title": product.title,
                "product_price": float(product.price),
                "product_currency": product.currency,
                "quantity": qty,
                "discount": prod.get('discount', 0),
                "rabat": prod.get('rabat', 0)
            })
    
    if not product_list:
        return json.dumps({
            "status": "error",
            "message": "Račun mora imati barem jedan proizvod s ispravnim product_name. Koristi filter_products_to_string za pregled dostupnih proizvoda."
        })
    
    # Set default date (today) - due_date is already validated as required
    invoice_date = date or timezone.now().date().strftime('%Y-%m-%d')
    invoice_due_date = due_date
    
    # Build display message
    products_summary = ", ".join([f"{p['product_title']} x{p['quantity']}" for p in product_list])
    
    # Set invoice type and payment method with defaults
    final_invoice_type = invoice_type if invoice_type in ['maloprodajni', 'veleprodajni'] else None
    final_payment_method = payment_method if payment_method in ['cash', 'card', 'bank_transfer', 'other'] else 'bank_transfer'
    
    return json.dumps({
        "status": "action_required",
        "action_type": "invoice_add",
        "action_data": {
            "number": number,
            "client_id": client.id,
            "client_name": client.clientName,
            "subject_id": subject.id,
            "subject_name": subject.clientName,
            "date": invoice_date,
            "due_date": invoice_due_date,
            "title": title,
            "notes": notes,
            "products": product_list,
            "invoice_type": final_invoice_type,
            "payment_method": final_payment_method
        },
        "display_message": f"Kreiraj račun - Broj: {number}, Klijent: {client.clientName}, Subjekt: {subject.clientName}, Datum: {invoice_date}, Datum dospijeća: {invoice_due_date}, Naslov: '{title}', Napomene: '{notes or 'N/A'}', Proizvodi: {products_summary}, Tip: {final_invoice_type or 'N/A'}, Način plaćanja: {final_payment_method}"
    })


def propose_offer_add(number=None, client_name=None, client_id=None, subject_name=None, subject_id=None,
                      date=None, due_date=None, title=None, notes=None, products=None):
    """
    Proposes creating a new offer/quote. Does NOT execute the change.
    Returns an action proposal that requires user confirmation.
    
    Offers are price proposals sent to clients - they are NOT invoices and don't require payment.
    The due_date on offers is an expiration date with no legal consequences if it passes.
    
    Parameters:
    - number: (REQUIRED) Broj ponude - unique identifier for the offer. Common Croatian practice is similar 
              to invoices: "P-2026-001" (P for ponuda + year + sequential) or following the same 
              format as invoices. Check existing offers with filter_offers_to_string to follow 
              the established numbering convention used by this business.
    - client_name: Ime klijenta (djelomično podudaranje) - provide this OR client_id (one is REQUIRED)
    - client_id: ID klijenta - provide this OR client_name (one is REQUIRED)
    - subject_name: Naziv subjekta/tvrtke izdavatelja (djelomično podudaranje) - provide this OR subject_id (one is REQUIRED)
    - subject_id: ID subjekta/tvrtke izdavatelja - provide this OR subject_name (one is REQUIRED)
    - date: Datum ponude u formatu YYYY-MM-DD - the offer date (defaults to today if not provided)
    - due_date: (REQUIRED) Datum isteka ponude u formatu YYYY-MM-DD - when the offer expires (typically 30 days after date)
    - title: (REQUIRED) Naslov ponude - brief description/title for the offer
    - notes: Napomene (opcionalno) - additional notes to appear on the offer
    - products: (REQUIRED) Lista proizvoda s količinama u formatu [{"product_name": "Naziv", "quantity": 1, "discount": 0, "rabat": 0}, ...]
                Svaki proizvod mora imati product_name i quantity. Polja discount i rabat su opcionalna.
                Koristi filter_products_to_string da pronađeš dostupne proizvode prije kreiranja ponude.
    """
    import json
    from datetime import datetime, timedelta
    
    # Validate required fields
    if not number:
        return json.dumps({
            "status": "error",
            "message": "Broj ponude (number) je obavezan parametar."
        })
    
    if not title:
        return json.dumps({
            "status": "error",
            "message": "Naslov ponude (title) je obavezan parametar."
        })
    
    if not due_date:
        return json.dumps({
            "status": "error",
            "message": "Datum isteka (due_date) je obavezan parametar u formatu YYYY-MM-DD."
        })
    
    if not client_name and not client_id:
        return json.dumps({
            "status": "error",
            "message": "Potrebno je navesti klijenta - client_name ili client_id."
        })
    
    if not subject_name and not subject_id:
        return json.dumps({
            "status": "error",
            "message": "Potrebno je navesti subjekt - subject_name ili subject_id."
        })
    
    if not products:
        return json.dumps({
            "status": "error",
            "message": "Lista proizvoda (products) je obavezna. Koristi filter_products_to_string za pregled dostupnih proizvoda."
        })
    
    # Find client
    client = None
    if client_id:
        try:
            client = Client.objects.get(id=client_id)
        except Client.DoesNotExist:
            return json.dumps({
                "status": "error",
                "message": f"Klijent s ID-em {client_id} nije pronađen."
            })
    elif client_name:
        clients = Client.objects.filter(clientName__icontains=client_name)
        if clients.count() == 0:
            return json.dumps({
                "status": "error",
                "message": f"Klijent s imenom '{client_name}' nije pronađen."
            })
        elif clients.count() > 1:
            names = ", ".join([c.clientName for c in clients[:5]])
            return json.dumps({
                "status": "error",
                "message": f"Pronađeno više klijenata s imenom '{client_name}': {names}. Molimo budite precizniji."
            })
        client = clients.first()
    
    # Find subject (company)
    subject = None
    if subject_id:
        try:
            subject = Company.objects.get(id=subject_id)
        except Company.DoesNotExist:
            return json.dumps({
                "status": "error",
                "message": f"Subjekt s ID-em {subject_id} nije pronađen."
            })
    elif subject_name:
        subjects = Company.objects.filter(clientName__icontains=subject_name)
        if subjects.count() == 0:
            return json.dumps({
                "status": "error",
                "message": f"Subjekt s nazivom '{subject_name}' nije pronađen."
            })
        elif subjects.count() > 1:
            names = ", ".join([s.clientName for s in subjects[:5]])
            return json.dumps({
                "status": "error",
                "message": f"Pronađeno više subjekata s nazivom '{subject_name}': {names}. Molimo budite precizniji."
            })
        subject = subjects.first()
    
    # Parse and validate products
    product_list = []
    if products:
        for prod in products:
            product_name = prod.get('product_name') or prod.get('name') or prod.get('title')
            if not product_name:
                continue
            
            found_products = Product.objects.filter(title__icontains=product_name)
            if found_products.count() == 0:
                return json.dumps({
                    "status": "error",
                    "message": f"Proizvod '{product_name}' nije pronađen. Koristi filter_products_to_string za pregled dostupnih proizvoda."
                })
            elif found_products.count() > 1:
                names = ", ".join([p.title for p in found_products[:5]])
                return json.dumps({
                    "status": "error",
                    "message": f"Pronađeno više proizvoda s nazivom '{product_name}': {names}. Molimo budite precizniji."
                })
            
            product = found_products.first()
            
            # Validate quantity is provided for each product
            qty = prod.get('quantity')
            if qty is None:
                return json.dumps({
                    "status": "error",
                    "message": f"Količina (quantity) je obavezna za proizvod '{product_name}'."
                })
            
            product_list.append({
                "product_id": product.id,
                "product_title": product.title,
                "product_price": float(product.price),
                "product_currency": product.currency,
                "quantity": qty,
                "discount": prod.get('discount', 0),
                "rabat": prod.get('rabat', 0)
            })
    
    if not product_list:
        return json.dumps({
            "status": "error",
            "message": "Ponuda mora imati barem jedan proizvod s ispravnim product_name. Koristi filter_products_to_string za pregled dostupnih proizvoda."
        })
    
    # Set default date (today) - due_date is already validated as required
    offer_date = date or timezone.now().date().strftime('%Y-%m-%d')
    offer_due_date = due_date
    
    # Build display message
    products_summary = ", ".join([f"{p['product_title']} x{p['quantity']}" for p in product_list])
    
    return json.dumps({
        "status": "action_required",
        "action_type": "offer_add",
        "action_data": {
            "number": number,
            "client_id": client.id,
            "client_name": client.clientName,
            "subject_id": subject.id,
            "subject_name": subject.clientName,
            "date": offer_date,
            "due_date": offer_due_date,
            "title": title,
            "notes": notes,
            "products": product_list
        },
        "display_message": f"Kreiraj ponudu - Broj: {number}, Klijent: {client.clientName}, Subjekt: {subject.clientName}, Datum: {offer_date}, Datum isteka: {offer_due_date}, Naslov: '{title}', Napomene: '{notes or 'N/A'}', Proizvodi: {products_summary}"
    })


# =============================================================================
# ACTION EXECUTION FUNCTIONS
# These functions actually execute the changes after user confirmation.
# They are called from views.py, not directly by the AI.
# =============================================================================

def execute_inventory_action(action_type, action_data):
    """
    Executes an inventory action after user confirmation.
    Returns a result message.
    """
    try:
        if action_type == "inventory_add":
            subject = Company.objects.get(id=action_data["subject_id"])
            item = Inventory.objects.create(
                title=action_data["title"],
                quantity=action_data["quantity"],
                subject=subject
            )
            return {
                "status": "success",
                "message": f"Stavka '{action_data['title']}' uspješno dodana u inventar."
            }
        
        elif action_type == "inventory_remove":
            item = Inventory.objects.get(id=action_data["item_id"])
            title = item.title
            item.delete()
            return {
                "status": "success",
                "message": f"Stavka '{title}' uspješno uklonjena iz inventara."
            }
        
        elif action_type == "inventory_update":
            item = Inventory.objects.get(id=action_data["item_id"])
            changes_made = []
            
            if "new_title" in action_data:
                old_title = item.title
                item.title = action_data["new_title"]
                changes_made.append(f"naziv promijenjen s '{old_title}' na '{action_data['new_title']}'")
            
            if "new_quantity" in action_data:
                old_qty = item.quantity
                item.quantity = action_data["new_quantity"]
                changes_made.append(f"količina promijenjena s {old_qty} na {action_data['new_quantity']}")
            
            item.save()
            return {
                "status": "success",
                "message": f"Stavka uspješno ažurirana: {', '.join(changes_made)}."
            }
        
        else:
            return {
                "status": "error",
                "message": f"Nepoznata vrsta akcije: {action_type}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Greška pri izvršavanju akcije: {str(e)}"
        }


def execute_invoice_action(action_type, action_data):
    """
    Executes an invoice action after user confirmation.
    Returns a result message.
    """
    from datetime import datetime
    from decimal import Decimal
    
    try:
        if action_type == "invoice_add":
            # Get client and subject
            client = Client.objects.get(id=action_data["client_id"])
            subject = Company.objects.get(id=action_data["subject_id"])
            
            # Parse dates
            invoice_date = datetime.strptime(action_data["date"], '%Y-%m-%d').date()
            due_date = datetime.strptime(action_data["due_date"], '%Y-%m-%d').date()
            
            # Create the invoice
            invoice = Invoice.objects.create(
                number=action_data["number"],
                client=client,
                subject=subject,
                date=invoice_date,
                dueDate=due_date,
                title=action_data.get("title"),
                notes=action_data.get("notes"),
                is_paid=False,
                invoice_type=action_data.get("invoice_type"),
                payment_method=action_data.get("payment_method", "bank_transfer")
            )
            
            # Create invoice products
            for prod in action_data.get("products", []):
                product = Product.objects.get(id=prod["product_id"])
                InvoiceProduct.objects.create(
                    invoice=invoice,
                    product=product,
                    quantity=Decimal(str(prod.get("quantity", 1))),
                    discount=Decimal(str(prod.get("discount", 0))),
                    rabat=Decimal(str(prod.get("rabat", 0)))
                )
            
            return {
                "status": "success",
                "message": f"Račun br. {action_data['number']} uspješno kreiran za klijenta {client.clientName}."
            }
        
        else:
            return {
                "status": "error",
                "message": f"Nepoznata vrsta akcije za račun: {action_type}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Greška pri kreiranju računa: {str(e)}"
        }


def execute_offer_action(action_type, action_data):
    """
    Executes an offer action after user confirmation.
    Returns a result message.
    """
    from datetime import datetime
    from decimal import Decimal
    
    try:
        if action_type == "offer_add":
            # Get client and subject
            client = Client.objects.get(id=action_data["client_id"])
            subject = Company.objects.get(id=action_data["subject_id"])
            
            # Parse dates
            offer_date = datetime.strptime(action_data["date"], '%Y-%m-%d').date()
            due_date = datetime.strptime(action_data["due_date"], '%Y-%m-%d').date()
            
            # Create the offer
            offer = Offer.objects.create(
                number=action_data["number"],
                client=client,
                subject=subject,
                date=offer_date,
                dueDate=due_date,
                title=action_data.get("title"),
                notes=action_data.get("notes")
            )
            
            # Create offer products
            for prod in action_data.get("products", []):
                product = Product.objects.get(id=prod["product_id"])
                OfferProduct.objects.create(
                    offer=offer,
                    product=product,
                    quantity=Decimal(str(prod.get("quantity", 1))),
                    discount=Decimal(str(prod.get("discount", 0))),
                    rabat=Decimal(str(prod.get("rabat", 0)))
                )
            
            return {
                "status": "success",
                "message": f"Ponuda br. {action_data['number']} uspješno kreirana za klijenta {client.clientName}."
            }
        
        else:
            return {
                "status": "error",
                "message": f"Nepoznata vrsta akcije za ponudu: {action_type}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Greška pri kreiranju ponude: {str(e)}"
        }


def get_company_from_court_registry(oib=None, name=None):
    """
    Fetches company data from the Croatian Court Registry (Sudski registar).
    Returns company data that can be used to populate a new client form.
    
    Parameters (at least one is REQUIRED):
    - oib: OIB number (11 digits) - provide this OR name
    - name: Company name to search for (minimum 3 characters) - provide this OR oib
    """
    import json
    from .utils.court_registry import (
        fetch_company_data_by_oib,
        search_companies_by_name,
        CourtRegistryError
    )
    
    # Validate at least one parameter
    if not oib and not name:
        return json.dumps({
            "status": "error",
            "message": "Molimo navedite OIB ili naziv tvrtke za pretraživanje."
        })
    
    try:
        if oib:
            # Validate OIB format
            oib = str(oib).strip()
            if len(oib) != 11 or not oib.isdigit():
                return json.dumps({
                    "status": "error",
                    "message": "OIB mora sadržavati točno 11 znamenki."
                })
            
            data = fetch_company_data_by_oib(oib, entity_type='client')
            return json.dumps({
                "status": "success",
                "data": data,
                "message": f"Pronađen subjekt: {data.get('clientName', 'N/A')}"
            })
        
        else:
            # Search by name
            name = str(name).strip()
            if len(name) < 3:
                return json.dumps({
                    "status": "error",
                    "message": "Naziv mora sadržavati najmanje 3 znaka."
                })
            
            results = search_companies_by_name(name, limit=10)
            if not results:
                return json.dumps({
                    "status": "not_found",
                    "message": f"Nije pronađen nijedan subjekt s nazivom '{name}'."
                })
            
            return json.dumps({
                "status": "success",
                "results": results,
                "count": len(results),
                "message": f"Pronađeno {len(results)} rezultata. Koristi OIB za dohvaćanje detaljnih podataka."
            })
    
    except CourtRegistryError as e:
        return json.dumps({
            "status": "error",
            "message": str(e)
        })
    
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Greška pri dohvaćanju podataka: {str(e)}"
        })


def propose_client_add(client_name, address, province, postal_code, email, client_unique_id=None,
                       client_type="Pravna osoba", oib=None, vat_id=None, phone=None):
    """
    Proposes adding a new client. Does NOT execute the change.
    Returns an action proposal that requires user confirmation.
    
    Parameters:
    - client_name: Name of the client (REQUIRED)
    - address: Street address (REQUIRED)
    - province: County/province - must match one of the Croatian counties (REQUIRED)
    - postal_code: 5-digit postal code (REQUIRED)
    - email: Email address (REQUIRED)
    - client_unique_id: 4-digit unique ID. If not provided, will be auto-generated based on existing clients.
    - client_type: 'Fizička osoba' or 'Pravna osoba' (default: 'Pravna osoba')
    - oib: 11-digit OIB number (optional for legal entities in Croatia)
    - vat_id: 13-character VAT ID, e.g. 'HR12345678901' (REQUIRED for Croatian companies)
    - phone: Phone number (optional)
    """
    import json
    
    # Validate required fields
    if not client_name:
        return json.dumps({
            "status": "error",
            "message": "Ime klijenta je obavezno."
        })
    
    if not address:
        return json.dumps({
            "status": "error",
            "message": "Adresa je obavezna."
        })
    
    if not province:
        return json.dumps({
            "status": "error",
            "message": "Županija je obavezna."
        })
    
    if not postal_code:
        return json.dumps({
            "status": "error",
            "message": "Poštanski broj je obavezan."
        })
    
    if not email:
        return json.dumps({
            "status": "error",
            "message": "Email adresa je obavezna."
        })
    
    if not vat_id:
        return json.dumps({
            "status": "error",
            "message": "VAT ID (porezni broj) je obavezan. Za hrvatske tvrtke koristi format HR + 11 znamenki OIB-a."
        })
    
    # Validate postal code format
    postal_code = str(postal_code).strip()
    if len(postal_code) != 5 or not postal_code.isdigit():
        return json.dumps({
            "status": "error",
            "message": "Poštanski broj mora sadržavati točno 5 znamenki."
        })
    
    # Validate OIB if provided
    if oib:
        oib = str(oib).strip()
        if len(oib) != 11 or not oib.isdigit():
            return json.dumps({
                "status": "error",
                "message": "OIB mora sadržavati točno 11 znamenki."
            })
        # Check if OIB already exists
        if Client.objects.filter(OIB=oib).exists():
            return json.dumps({
                "status": "error",
                "message": f"Klijent s OIB-om {oib} već postoji u bazi."
            })
    
    # Validate VAT ID format
    vat_id = str(vat_id).strip().upper()
    if len(vat_id) != 13:
        return json.dumps({
            "status": "error",
            "message": "VAT ID mora sadržavati točno 13 znakova (npr. HR12345678901)."
        })
    # Check if VAT ID already exists
    if Client.objects.filter(VATID=vat_id).exists():
        return json.dumps({
            "status": "error",
            "message": f"Klijent s VAT ID-om {vat_id} već postoji u bazi."
        })
    
    # Validate client type
    valid_types = ['Fizička osoba', 'Pravna osoba']
    if client_type not in valid_types:
        return json.dumps({
            "status": "error",
            "message": f"Tip klijenta mora biti jedan od: {', '.join(valid_types)}"
        })
    
    # Validate province
    valid_provinces = [
        'ZAGREBAČKA ŽUPANIJA', 'KRAPINSKO-ZAGORSKA ŽUPANIJA', 'SISAČKO-MOSLAVAČKA ŽUPANIJA',
        'KARLOVAČKA ŽUPANIJA', 'VARAŽDINSKA ŽUPANIJA', 'KOPRIVNIČKO-KRIŽEVAČKA ŽUPANIJA',
        'BJELOVARSKO-BILOGORSKA ŽUPANIJA', 'PRIMORSKO-GORANSKA ŽUPANIJA', 'LIČKO-SENJSKA ŽUPANIJA',
        'VIROVITIČKO-PODRAVSKA ŽUPANIJA', 'POŽEŠKO-SLAVONSKA ŽUPANIJA', 'BRODSKO-POSAVSKA ŽUPANIJA',
        'ZADARSKA ŽUPANIJA', 'OSJEČKO-BARANJSKA ŽUPANIJA', 'ŠIBENSKO-KNINSKA ŽUPANIJA',
        'VUKOVARSKO-SRIJEMSKA ŽUPANIJA', 'SPLITSKO-DALMATINSKA ŽUPANIJA', 'ISTARSKA ŽUPANIJA',
        'DUBROVAČKO-NERETVANSKA ŽUPANIJA', 'MEĐIMURSKA ŽUPANIJA', 'GRAD ZAGREB',
        'INOZEMSTVO / NIJE PRIMJENJIVO'
    ]
    province_upper = province.upper().strip()
    if province_upper not in valid_provinces:
        # Try to find a partial match
        matched = [p for p in valid_provinces if province_upper in p]
        if matched:
            province = matched[0]
        else:
            return json.dumps({
                "status": "error",
                "message": f"Nepoznata županija: {province}. Dostupne županije: {', '.join(valid_provinces[:5])}..."
            })
    else:
        province = province_upper
    
    # Generate client_unique_id if not provided
    if not client_unique_id:
        existing_ids = Client.objects.values_list('clientUniqueId', flat=True)
        existing_ids = [int(id) for id in existing_ids if id and id.isdigit()]
        if existing_ids:
            next_id = max(existing_ids) + 1
        else:
            next_id = 1
        client_unique_id = str(next_id).zfill(4)
    else:
        client_unique_id = str(client_unique_id).strip().zfill(4)
        if not client_unique_id.isdigit() or len(client_unique_id) != 4:
            return json.dumps({
                "status": "error",
                "message": "ID klijenta mora biti 4-znamenkasti broj."
            })
        # Check if ID already exists
        if Client.objects.filter(clientUniqueId=client_unique_id).exists():
            return json.dumps({
                "status": "error",
                "message": f"Klijent s ID-om {client_unique_id} već postoji. Sljedeći dostupni ID će biti automatski dodijeljen."
            })
    
    return json.dumps({
        "status": "action_required",
        "action_type": "client_add",
        "action_data": {
            "clientName": client_name,
            "addressLine1": address,
            "province": province,
            "postalCode": postal_code,
            "emailAddress": email,
            "clientUniqueId": client_unique_id,
            "clientType": client_type,
            "OIB": oib,
            "VATID": vat_id,
            "phoneNumber": phone
        },
        "display_message": f"Dodaj klijenta - Ime: '{client_name}', Adresa: '{address}', Županija: '{province}', Poštanski broj: {postal_code}, Email: '{email}', ID: {client_unique_id}, Tip: '{client_type}', OIB: '{oib or 'N/A'}', VAT ID: '{vat_id}', Telefon: '{phone or 'N/A'}'"
    })


def execute_client_action(action_type, action_data):
    """
    Executes a client action after user confirmation.
    Returns a result message.
    """
    try:
        if action_type == "client_add":
            # Create the client
            client = Client.objects.create(
                clientName=action_data["clientName"],
                addressLine1=action_data["addressLine1"],
                province=action_data["province"],
                postalCode=action_data["postalCode"],
                emailAddress=action_data["emailAddress"],
                clientUniqueId=action_data["clientUniqueId"],
                clientType=action_data["clientType"],
                OIB=action_data.get("OIB"),
                VATID=action_data["VATID"],
                phoneNumber=action_data.get("phoneNumber")
            )
            
            return {
                "status": "success",
                "message": f"Klijent '{client.clientName}' (ID: {client.clientUniqueId}) uspješno kreiran."
            }
        
        else:
            return {
                "status": "error",
                "message": f"Nepoznata vrsta akcije za klijenta: {action_type}"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Greška pri kreiranju klijenta: {str(e)}"
        }
