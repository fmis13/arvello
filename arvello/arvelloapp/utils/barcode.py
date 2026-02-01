"""
HUB3 2D barcode generator for Croatian payment slips.

Per HUB3 specification: https://hub.hr/sites/default/files/inline-files/2DBK_EUR_Uputa_1.pdf

Format: HRVHUB30 header followed by structured fields with LF (0x0A) separator.
Barcode type: PDF417
"""
import decimal
from io import BytesIO
from typing import Optional

from pdf417gen import encode, render_image


def _pad_or_truncate(text: str, length: int) -> str:
    """Pad with spaces or truncate string to exact length."""
    if text is None:
        text = ""
    # Normalize and truncate/pad
    text = str(text).strip()
    if len(text) > length:
        return text[:length]
    return text


def _format_amount(amount: decimal.Decimal) -> str:
    """
    Format amount for HUB3: 15 characters, right-aligned, zero-padded.
    Amount is in cents (smallest currency unit).
    """
    # Convert to cents (multiply by 100)
    cents = int(amount * 100)
    return str(cents).zfill(15)


def generate_hub3_data(
    iban: str,
    amount: decimal.Decimal,
    payer_name: str,
    payer_address: str,
    payer_city: str,
    receiver_name: str,
    receiver_address: str,
    receiver_city: str,
    reference_model: str = "HR99",
    reference_number: str = "",
    purpose_code: str = "OTHR",
    description: str = "",
    currency: str = "EUR"
) -> str:
    """
    Generate HUB3 barcode data string per specification.
    
    The HUB3 format consists of:
    - HRVHUB30 header
    - Currency (3 chars) - always EUR since 2023
    - Amount (15 chars) - in cents, zero-padded
    - Payer name (30 chars)
    - Payer address (27 chars)
    - Payer city (27 chars)
    - Receiver name (25 chars)
    - Receiver address (25 chars)
    - Receiver city (27 chars)
    - IBAN (21 chars)
    - Reference model (4 chars) - e.g., HR00, HR01, HR99
    - Reference number (22 chars)
    - Purpose code (4 chars) - e.g., OTHR, SALA, etc.
    - Description (35 chars)
    
    Fields are separated by LF (0x0A).
    """
    # Build the data string with LF separators
    lines = [
        "HRVHUB30",                                    # Header
        currency.upper()[:3].ljust(3),                 # Currency (EUR)
        _format_amount(amount),                        # Amount in cents
        _pad_or_truncate(payer_name, 30),             # Payer name
        _pad_or_truncate(payer_address, 27),          # Payer address
        _pad_or_truncate(payer_city, 27),             # Payer city
        _pad_or_truncate(receiver_name, 25),          # Receiver name
        _pad_or_truncate(receiver_address, 25),       # Receiver address
        _pad_or_truncate(receiver_city, 27),          # Receiver city
        _pad_or_truncate(iban, 21),                   # IBAN (no spaces)
        _pad_or_truncate(reference_model.upper(), 4), # Reference model
        _pad_or_truncate(reference_number, 22),       # Reference number
        _pad_or_truncate(purpose_code.upper(), 4),    # Purpose code
        _pad_or_truncate(description, 35),            # Description
    ]
    
    return "\n".join(lines)


def generate_hub3_barcode(
    iban: str,
    amount: decimal.Decimal,
    payer_name: str,
    payer_address: str,
    payer_city: str,
    receiver_name: str,
    receiver_address: str,
    receiver_city: str,
    reference_model: str = "HR99",
    reference_number: str = "",
    purpose_code: str = "OTHR",
    description: str = "",
    currency: str = "EUR",
    scale: int = 3,
    ratio: int = 3,
    padding: int = 20,
    fg_color: str = "#000000",
    bg_color: str = "#FFFFFF"
) -> bytes:
    """
    Generate HUB3 PDF417 barcode as PNG image bytes.
    
    Args:
        iban: Receiver's IBAN (without spaces)
        amount: Payment amount as Decimal
        payer_name: Payer's name (max 30 chars)
        payer_address: Payer's address (max 27 chars)
        payer_city: Payer's city with postal code (max 27 chars)
        receiver_name: Receiver's name (max 25 chars)
        receiver_address: Receiver's address (max 25 chars)
        receiver_city: Receiver's city with postal code (max 27 chars)
        reference_model: Payment reference model (e.g., HR00, HR01)
        reference_number: Payment reference number
        purpose_code: ISO 20022 purpose code (e.g., OTHR, SALA)
        description: Payment description (max 35 chars)
        currency: Currency code (default EUR)
        scale: Barcode scale factor
        ratio: Barcode aspect ratio
        padding: Padding around barcode in pixels
        fg_color: Foreground (barcode) color as hex
        bg_color: Background color as hex
    
    Returns:
        PNG image as bytes
    """
    # Remove spaces from IBAN
    iban_clean = iban.replace(" ", "").upper()
    
    # Generate the data string
    data = generate_hub3_data(
        iban=iban_clean,
        amount=amount,
        payer_name=payer_name,
        payer_address=payer_address,
        payer_city=payer_city,
        receiver_name=receiver_name,
        receiver_address=receiver_address,
        receiver_city=receiver_city,
        reference_model=reference_model,
        reference_number=reference_number,
        purpose_code=purpose_code,
        description=description,
        currency=currency
    )
    
    # Encode as PDF417
    codes = encode(
        data,
        columns=8,  # Recommended for HUB3
        security_level=2  # Error correction level
    )
    
    # Render to image - pdf417gen expects hex color strings
    image = render_image(
        codes,
        scale=scale,
        ratio=ratio,
        padding=padding,
        fg_color=fg_color,
        bg_color=bg_color
    )
    
    # Convert to PNG bytes
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer.getvalue()


def generate_hub3_barcode_base64(
    iban: str,
    amount: decimal.Decimal,
    payer_name: str,
    payer_address: str,
    payer_city: str,
    receiver_name: str,
    receiver_address: str,
    receiver_city: str,
    reference_model: str = "HR99",
    reference_number: str = "",
    purpose_code: str = "OTHR",
    description: str = "",
    currency: str = "EUR",
    **kwargs
) -> str:
    """
    Generate HUB3 PDF417 barcode as base64 encoded PNG string.
    
    Same arguments as generate_hub3_barcode.
    
    Returns:
        Base64 encoded PNG image string (ready for use in HTML img src)
    """
    import base64
    
    png_bytes = generate_hub3_barcode(
        iban=iban,
        amount=amount,
        payer_name=payer_name,
        payer_address=payer_address,
        payer_city=payer_city,
        receiver_name=receiver_name,
        receiver_address=receiver_address,
        receiver_city=receiver_city,
        reference_model=reference_model,
        reference_number=reference_number,
        purpose_code=purpose_code,
        description=description,
        currency=currency,
        **kwargs
    )
    
    return base64.b64encode(png_bytes).decode('utf-8')
