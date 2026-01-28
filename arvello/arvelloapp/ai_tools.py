from .models import Invoice, InvoiceProduct, Product, Supplier, Expense, Company, Inventory, Client
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
    }
    
    model_name = criteria.get('model_name', '') or ''
    model_name = model_name.lower() if model_name else ''
    
    # Determine which models to query
    if model_name and model_name in model_mapping:
        models_to_query = {model_name: model_mapping[model_name]}
    elif model_name and model_name not in model_mapping:
        return f"Unknown model: {model_name}. Available models: Invoice, Client, Product, Expense, Supplier, Company, Inventory"
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
    