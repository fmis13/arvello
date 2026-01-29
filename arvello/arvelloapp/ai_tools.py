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
        queryset = queryset.filter(title__icontains=criteria['title'])
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

def propose_inventory_add(title, quantity, subject_name=None, subject_id=None):
    """
    Proposes adding a new inventory item. Does NOT execute the change.
    Returns an action proposal that requires user confirmation.
    
    Parameters:
    - title: Name/title of the inventory item to add
    - quantity: Quantity to add
    - subject_name: Name of the subject/company (partial match)
    - subject_id: ID of the subject/company (alternative to name)
    """
    import json
    
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
    else:
        # Try to get the first (and possibly only) company
        subjects = Company.objects.all()
        if subjects.count() == 1:
            subject = subjects.first()
        else:
            return json.dumps({
                "status": "error",
                "message": "Molimo navedite subjekt za koji želite dodati stavku inventara."
            })
    
    return json.dumps({
        "status": "action_required",
        "action_type": "inventory_add",
        "action_data": {
            "title": title,
            "quantity": quantity,
            "subject_id": subject.id,
            "subject_name": subject.clientName
        },
        "display_message": f"Dodaj '{title}' (količina: {quantity}) u inventar subjekta {subject.clientName}"
    })


def propose_inventory_remove(item_title=None, item_id=None):
    """
    Proposes removing an inventory item. Does NOT execute the change.
    Returns an action proposal that requires user confirmation.
    
    Parameters:
    - item_title: Title of the item to remove (partial match)
    - item_id: ID of the item to remove (alternative to title)
    """
    import json
    
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
    else:
        return json.dumps({
            "status": "error",
            "message": "Molimo navedite naziv ili ID stavke koju želite ukloniti."
        })
    
    return json.dumps({
        "status": "action_required",
        "action_type": "inventory_remove",
        "action_data": {
            "item_id": item.id,
            "title": item.title,
            "quantity": item.quantity,
            "subject_name": item.subject.clientName if item.subject else "N/A"
        },
        "display_message": f"Ukloni '{item.title}' (količina: {item.quantity}) iz inventara"
    })


def propose_inventory_update(item_title=None, item_id=None, new_title=None, new_quantity=None):
    """
    Proposes updating an inventory item. Does NOT execute the change.
    Returns an action proposal that requires user confirmation.
    
    Parameters:
    - item_title: Title of the item to update (partial match)
    - item_id: ID of the item to update (alternative to title)
    - new_title: New title for the item (optional)
    - new_quantity: New quantity for the item (optional)
    """
    import json
    
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
    else:
        return json.dumps({
            "status": "error",
            "message": "Molimo navedite naziv ili ID stavke koju želite promijeniti."
        })
    
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
    
    if not changes:
        return json.dumps({
            "status": "error",
            "message": "Niste naveli nikakve promjene. Navedite novi naziv ili novu količinu."
        })
    
    return json.dumps({
        "status": "action_required",
        "action_type": "inventory_update",
        "action_data": action_data,
        "display_message": f"Promijeni {' i '.join(changes)} za stavku '{item.title}'"
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
