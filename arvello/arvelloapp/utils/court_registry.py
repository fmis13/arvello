"""
Court Registry (Sudski registar) API integration for Croatia.

API Documentation: https://sudreg-data.gov.hr/api/javni/dokumentacija/open_api
Base URL: https://sudreg-data.gov.hr/api/javni
Test Environment: https://sudreg-data-test.gov.hr/api/javni

The Croatian Court Registry API provides access to company registration data.
Uses OAuth2 Client Credentials flow for authentication.
Token endpoint: https://sudreg-data.gov.hr/api/oauth/token
"""

import requests
import re
from requests.auth import HTTPBasicAuth
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class CompanyData:
    """Data class for company information from the court registry."""
    oib: Optional[str] = None
    mbs: Optional[str] = None  # Matični broj subjekta
    name: Optional[str] = None
    short_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    county: Optional[str] = None  # Županija
    legal_form: Optional[str] = None  # Pravni oblik
    main_activity: Optional[str] = None  # Glavna djelatnost
    registration_date: Optional[str] = None
    capital: Optional[str] = None
    status: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    raw_data: Optional[Dict] = None


_PHONE_KEYS = {
    'telefon', 'tel', 'telefonBroj', 'brojTelefona', 'telefon1', 'telefon2',
    'mobitel', 'gsm', 'kontaktTelefon', 'kontakt_tel', 'phone'
}
_EMAIL_KEYS = {
    'email', 'e-mail', 'e_mail', 'mail', 'emailAdresa', 'email_adresa',
    'kontaktEmail'
}
_PHONE_TYPE_HINTS = {'telefon', 'mobitel', 'phone', 'tel', 'gsm'}
_EMAIL_TYPE_HINTS = {'email', 'e-mail', 'mail'}


# Croatian legal form suffixes - used to clean company names
LEGAL_FORMS = [
    r'd\.o\.o\.',
    r'j\.d\.o\.o\.',
    r'd\.d\.',
    r'j\.t\.d\.',
    r'k\.d\.',
    r'z\.o\.o\.',
    r'OBRT',
    r'vl\.',
]

# Compiled pattern to match legal form followed by optional descriptive text
_LEGAL_FORM_PATTERN = re.compile(
    r'(' + '|'.join(LEGAL_FORMS) + r')\s*.*$',
    re.IGNORECASE
)


def clean_company_name(name: Optional[str]) -> Optional[str]:
    """
    Clean company name by removing descriptive suffix after legal form identifier.
    
    Examples:
    - "VODOVOD DUBROVNIK d.o.o. za vodoopskrbu i komunalnu hidrotehniku" -> "VODOVOD DUBROVNIK d.o.o."
    - "PRIMJER d.d. za trgovinu" -> "PRIMJER d.d."
    - "OBRT ZA USLUGE vl. Ivan Horvat" -> "OBRT"
    
    Args:
        name: Company name that may include descriptive suffix
        
    Returns:
        Cleaned company name with legal form kept but description removed
    """
    if not name:
        return name
    
    # Try to find a legal form and truncate after it
    match = _LEGAL_FORM_PATTERN.search(name)
    if match:
        # Return everything up to and including the legal form
        legal_form_end = match.start(1) + len(match.group(1))
        cleaned = name[:legal_form_end].strip()
        return cleaned if cleaned else name
    
    return name


def _clean_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        for item in value:
            cleaned = _clean_string(item)
            if cleaned:
                return cleaned
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return _clean_string(str(value))


def _coalesce_value(*values: Any) -> Optional[str]:
    for value in values:
        cleaned = _clean_string(value)
        if cleaned:
            return cleaned
    return None


def _find_value_by_keys(payload: Any, keys: set) -> Optional[str]:
    if isinstance(payload, dict):
        for key in keys:
            if key in payload and payload[key]:
                return _clean_string(payload[key])
        for value in payload.values():
            found = _find_value_by_keys(value, keys)
            if found:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_value_by_keys(item, keys)
            if found:
                return found
    return None


def _find_contact_by_type(payload: Any, type_hints: set) -> Optional[str]:
    if isinstance(payload, dict):
        type_value = payload.get('vrsta') or payload.get('tip') or payload.get('type') or payload.get('oznaka')
        value = payload.get('vrijednost') or payload.get('value') or payload.get('kontakt') or payload.get('podatak')
        if type_value and value and isinstance(type_value, str):
            lowered = type_value.lower()
            if any(hint in lowered for hint in type_hints):
                return _clean_string(value)
        for item in payload.values():
            found = _find_contact_by_type(item, type_hints)
            if found:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_contact_by_type(item, type_hints)
            if found:
                return found
    return None


def _extract_contact_value(payload: Any, keys: set, type_hints: set) -> Optional[str]:
    return _coalesce_value(
        _find_value_by_keys(payload, keys),
        _find_contact_by_type(payload, type_hints)
    )


def _extract_address_components(data: Dict[str, Any]) -> tuple[Optional[str], Optional[str], Optional[str], Any]:
    address_data = (
        data.get('sjediste')
        or data.get('adresa')
        or data.get('poslovnaAdresa')
        or data.get('adresaSjedista')
        or data.get('mjestoSjedista')
        or {}
    )
    if isinstance(address_data, list):
        address_data = address_data[0] if address_data else {}

    address = None
    city = None
    postal_code = None

    if isinstance(address_data, dict):
        address, city, postal_code = _extract_address_from_dict(address_data)
    elif isinstance(address_data, str):
        address, city, postal_code = _extract_address_from_string(address_data)

    if not city:
        city = _coalesce_value(
            _find_value_by_keys(data, {'mjesto', 'grad', 'naselje', 'nazivMjesta', 'mjestoNaziv'}),
            _find_value_by_keys(address_data, {'mjesto', 'grad', 'naselje', 'nazivMjesta', 'mjestoNaziv'})
        )
    if not postal_code:
        postal_code = _coalesce_value(
            _find_value_by_keys(data, {'postanskiBroj', 'postanski_broj', 'postanskiBrojMjesta'}),
            _find_value_by_keys(address_data, {'postanskiBroj', 'postanski_broj', 'postanskiBrojMjesta'})
        )

    return _clean_string(address), _clean_string(city), _clean_string(postal_code), address_data


def _extract_address_from_dict(address_data: Dict[str, Any]) -> tuple[Optional[str], Optional[str], Optional[str]]:
    street = _coalesce_value(
        address_data.get('ulica'),
        address_data.get('ulicaNaziv'),
        address_data.get('nazivUlice'),
        address_data.get('ulicaPuna'),
        address_data.get('nazivUlicePuna')
    )
    number = _coalesce_value(
        address_data.get('kucniBroj'),
        address_data.get('kucni_broj'),
        address_data.get('broj'),
        address_data.get('brojKuce')
    )
    number_suffix = _coalesce_value(
        address_data.get('kucniBrojDodatak'),
        address_data.get('brojKuceDodatak')
    )
    if number_suffix and number and number_suffix not in number:
        number = f"{number}{number_suffix}"

    address_parts = [part for part in [street, number] if part]
    address = ' '.join(address_parts) if address_parts else _clean_string(address_data.get('adresa'))

    city = _coalesce_value(
        address_data.get('mjesto'),
        address_data.get('grad'),
        address_data.get('naselje'),
        address_data.get('nazivMjesta'),
        address_data.get('mjestoNaziv')
    )
    postal_code = _coalesce_value(
        address_data.get('postanskiBroj'),
        address_data.get('postanski_broj'),
        address_data.get('postanskiBrojMjesta'),
        _extract_postal_code_from_post_office(address_data)
    )

    return address, city, postal_code


def _extract_postal_code_from_post_office(address_data: Dict[str, Any]) -> Optional[str]:
    post_office = address_data.get('postanskiUred') or address_data.get('postanski_ured')
    if isinstance(post_office, dict):
        return _coalesce_value(post_office.get('broj'), post_office.get('postanskiBroj'))
    return None


def _extract_address_from_string(address_text: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    cleaned = _clean_string(address_text)
    if not cleaned:
        return None, None, None

    parts = [part.strip() for part in re.split(r'[\n,;]+', cleaned) if part.strip()]
    address = parts[0] if parts else cleaned
    postal_code = None
    city = None

    for part in parts[1:]:
        match = re.search(r'(\d{5})\s*(.*)', part)
        if match:
            postal_code = match.group(1)
            city = match.group(2).strip() if match.group(2) else None
            break

    if not postal_code:
        match = re.search(r'(\d{5})\s+([^\d,]+)', cleaned)
        if match:
            postal_code = match.group(1)
            city = match.group(2).strip()

    return address, city, postal_code


def _normalize_county_name(value: str) -> Optional[str]:
    cleaned = _clean_string(value)
    if not cleaned:
        return None
    cleaned = re.sub(r'\s*\([^)]*\)', '', cleaned)
    cleaned = cleaned.replace(',', ' ')
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip().upper()


def _extract_county(data: Dict[str, Any], address_data: Any) -> Optional[str]:
    candidates: List[str] = []

    def add_candidate(value: Any) -> None:
        if not value:
            return
        if isinstance(value, dict):
            for key in ('naziv', 'ime', 'nazivZupanije', 'zupanijaNaziv'):
                if value.get(key):
                    add_candidate(value.get(key))
            return
        if isinstance(value, list):
            for item in value:
                add_candidate(item)
            return
        if isinstance(value, str):
            candidates.append(value)

    for source in (data, address_data):
        if isinstance(source, dict):
            for key in (
                'zupanija', 'zupanijaNaziv', 'zupanija_naziv', 'nazivZupanije',
                'zupanijaOznaka', 'zupanijaSifra', 'sifraZupanije',
                'zupanijaNazivSkraceno', 'zupanijaOpis', 'zupanijaIme'
            ):
                add_candidate(source.get(key))

    add_candidate(_find_value_by_keys(data, {'zupanija', 'zupanijaNaziv', 'zupanija_naziv', 'nazivZupanije'}))

    for candidate in candidates:
        normalized = _normalize_county_name(candidate)
        if normalized:
            return normalized

    return None


class CourtRegistryClient:
    """
    Client for Croatian Court Registry (Sudski registar) API.
    
    The API is available at https://sudreg-data.gov.hr/api/javni
    Authentication uses OAuth2 Client Credentials flow.
    
    API Documentation:
    - https://sudreg-data.gov.hr/api/javni/dokumentacija/open_api
    
    Endpoints:
    - /subjekti?oib={oib} - Search by OIB
    - /subjekti?naziv={name} - Search by name
    - /subjekti/{mbs} - Get by MBS number
    """
    
    # Base URLs
    BASE_URL = "https://sudreg-data.gov.hr/api/javni"
    SANDBOX_URL = "https://sudreg-data-test.gov.hr/api/javni"
    
    # OAuth2 token endpoints
    TOKEN_URL = "https://sudreg-data.gov.hr/api/oauth/token"
    SANDBOX_TOKEN_URL = "https://sudreg-data-test.gov.hr/api/oauth/token"
    
    # Timeout for API requests (seconds)
    TIMEOUT = 30
    
    # Cache timeout (seconds) - cache results for 1 hour
    CACHE_TIMEOUT = 3600
    
    # Token expires in 6 hours, but refresh 5 minutes early
    TOKEN_REFRESH_BUFFER = 300
    
    def __init__(
        self, 
        client_id: Optional[str] = None, 
        client_secret: Optional[str] = None, 
        use_sandbox: bool = False,
        config: Optional[Any] = None
    ):
        """
        Initialize the Court Registry client.
        
        Args:
            client_id: Client ID for OAuth2 authentication
            client_secret: Client Secret for OAuth2 authentication
            use_sandbox: Whether to use sandbox/test environment
            config: CourtRegistryConfig model instance for token caching
        """
        # Strip whitespace from credentials (common user error)
        self.client_id = client_id.strip() if client_id else None
        self.client_secret = client_secret.strip() if client_secret else None
        self.use_sandbox = use_sandbox
        self.config = config  # For persisting token cache
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        # Load cached token from config if available
        if config and config.token_cache and config.token_expires_at:
            if config.token_expires_at > timezone.now():
                self._access_token = config.token_cache
                self._token_expires_at = config.token_expires_at
        
        self.session = requests.Session()
        
        # Set up headers
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'Arvello/1.0'
        })
    
    def _get_base_url(self) -> str:
        """Get the base URL based on sandbox setting."""
        return self.SANDBOX_URL if self.use_sandbox else self.BASE_URL
    
    def _get_token_url(self) -> str:
        """Get the token URL based on sandbox setting."""
        return self.SANDBOX_TOKEN_URL if self.use_sandbox else self.TOKEN_URL
    
    def _get_access_token(self, force_refresh: bool = False) -> Optional[str]:
        """
        Get a valid OAuth2 access token, refreshing if necessary.
        
        Args:
            force_refresh: Force token refresh even if cached token is valid
        
        Returns:
            Access token string
            
        Raises:
            CourtRegistryError: If credentials are missing or invalid
        """
        if not self.client_id or not self.client_secret:
            raise CourtRegistryError(
                "API podaci za Sudski registar nisu konfigurirani. "
                "Molimo postavite Client ID i Client Secret u administraciji."
            )
        
        # Check if we have a valid cached token (unless force refresh requested)
        if not force_refresh and self._access_token and self._token_expires_at:
            # Refresh if token expires within buffer time
            if self._token_expires_at > timezone.now() + timedelta(seconds=self.TOKEN_REFRESH_BUFFER):
                return self._access_token
        
        # Request new token using client credentials flow
        try:
            token_url = self._get_token_url()
            response = requests.post(
                token_url,
                auth=HTTPBasicAuth(self.client_id, self.client_secret),
                data={'grant_type': 'client_credentials'},
                timeout=self.TIMEOUT,
                verify=True
            )
            response.raise_for_status()
            
            token_data = response.json()
            if isinstance(token_data, list):
                if not token_data:
                    raise CourtRegistryError("Prazan odgovor od token servera.")
                token_data = token_data[0]
            
            if not isinstance(token_data, dict):
                raise CourtRegistryError("Neispravan format tokena primljen od servera.")
                
            self._access_token = token_data.get('access_token')
            
            # Token typically expires in 6 hours (21600 seconds)
            expires_in = token_data.get('expires_in', 21600)
            self._token_expires_at = timezone.now() + timedelta(seconds=expires_in)
            
            # Persist token to database if config is available
            if self.config:
                self.config.token_cache = self._access_token
                self.config.token_expires_at = self._token_expires_at
                self.config.save(update_fields=['token_cache', 'token_expires_at'])
                logger.debug(f"OAuth2 token cached, expires at {self._token_expires_at}")
            
            return self._access_token
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else None
            response_text = ""
            try:
                if e.response is not None:
                    response_text = e.response.text[:500]
            except:
                pass
            logger.error(f"Failed to obtain OAuth2 token: HTTP {status_code} - {response_text}")
            if status_code == 401:
                raise CourtRegistryError(
                    "Neispravni OAuth2 podaci (client_id/client_secret). "
                    "Provjerite jeste li ispravno unijeli podatke bez razmaka na početku ili kraju."
                )
            elif status_code is None:
                raise CourtRegistryError(f"Neuspjeli zahtjev za token bez odgovora: {str(e)}")
            raise CourtRegistryError(f"Greška pri dohvaćanju tokena: HTTP {status_code}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obtaining OAuth2 token: {e}")
            raise CourtRegistryError(f"Greška pri dohvaćanju tokena: {str(e)}")
    
    def _make_request(
        self, 
        endpoint: str, 
        method: str = 'GET', 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        _retry_on_401: bool = True
    ) -> Optional[Dict]:
        """
        Make an API request to the court registry.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            params: Query parameters
            data: Request body data
            _retry_on_401: Internal flag to prevent infinite retry loops
            
        Returns:
            Response data as dictionary or None on error
        """
        base_url = self._get_base_url()
        url = f"{base_url}/{endpoint.lstrip('/')}"
        
        # Get OAuth2 token and set Bearer auth header
        headers = {}
        access_token = self._get_access_token()
        headers['Authorization'] = f'Bearer {access_token}'
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, headers=headers, timeout=self.TIMEOUT)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params, json=data, headers=headers, timeout=self.TIMEOUT)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout while accessing court registry API: {url}")
            raise CourtRegistryError("API zahtjev je istekao. Pokušajte ponovo.")
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to court registry API: {url} - {e}")
            raise CourtRegistryError("Nije moguće povezati se s API-jem sudskog registra.")
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else None
            response_text = ""
            try:
                if e.response is not None:
                    response_text = e.response.text[:500]  # First 500 chars
            except:
                pass
            logger.error(f"HTTP error from court registry API: {status_code} - {e} - Response: {response_text}")
            
            if status_code == 401:
                # Token may have expired - attempt refresh and retry once
                if _retry_on_401:
                    logger.info("Received 401, attempting token refresh and retry")
                    # Clear cached token and force refresh
                    self._access_token = None
                    self._token_expires_at = None
                    try:
                        self._get_access_token(force_refresh=True)
                        # Retry the request once with new token
                        return self._make_request(
                            endpoint, method, params, data, _retry_on_401=False
                        )
                    except CourtRegistryError:
                        # Token refresh failed, raise original error
                        pass
                raise CourtRegistryError(
                    "Neispravni API podaci za autentifikaciju (401). "
                    "Provjerite Client ID i Client Secret te da su podaci ispravno uneseni bez razmaka."
                )
            elif status_code == 403:
                raise CourtRegistryError("Pristup API-ju nije dozvoljen (403).")
            elif status_code == 404:
                raise CourtRegistryError("Subjekt nije pronađen u registru (404).")
            elif status_code == 429:
                raise CourtRegistryError("Previše zahtjeva (429). Pokušajte ponovo kasnije.")
            elif status_code is None:
                raise CourtRegistryError(f"Neuspjeli HTTP zahtjev bez odgovora: {str(e)}")
            else:
                raise CourtRegistryError(f"Greška API-ja: HTTP {status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error to court registry API: {e}")
            raise CourtRegistryError(f"Greška pri komunikaciji s API-jem: {str(e)}")
        
        except ValueError as e:
            logger.error(f"JSON decode error from court registry API: {e}")
            raise CourtRegistryError("Neispravan odgovor od API-ja.")
    
    def search_by_oib(self, oib: str) -> Optional[CompanyData]:
        """
        Search for a company by OIB (Personal Identification Number).
        
        Uses the /detalji_subjekta endpoint which properly filters by OIB.
        
        Args:
            oib: 11-digit OIB number
            
        Returns:
            CompanyData object or None if not found
        """
        if not oib or len(oib) != 11 or not oib.isdigit():
            raise CourtRegistryError("OIB mora sadržavati točno 11 znamenki.")
        
        # Check cache first
        cache_key = f"court_registry_oib_{oib}"
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Returning cached data for OIB {oib}")
            return cached_data
        
        try:
            # Use detalji_subjekta endpoint with OIB identifier
            # This correctly filters by OIB unlike /subjekti?oib=
            response = self._make_request(
                '/detalji_subjekta',
                params={
                    'tip_identifikatora': 'oib',
                    'identifikator': oib
                }
            )
            
            if response:
                # detalji_subjekta returns a single object, not a list
                company_data = self._parse_details_response(response)
                if company_data:
                    cache.set(cache_key, company_data, self.CACHE_TIMEOUT)
                return company_data
                
        except CourtRegistryError:
            raise
        except Exception as e:
            logger.error(f"Error searching by OIB {oib}: {e}")
            raise CourtRegistryError(f"Greška pri pretraživanju: {str(e)}")
        
        return None
    
    def _parse_details_response(self, data: Dict) -> Optional[CompanyData]:
        """
        Parse detalji_subjekta API response into CompanyData object.
        
        The detalji_subjekta endpoint returns a different structure than /subjekti:
        - Company name in tvrtka.ime
        - Short name in skracena_tvrtka.ime  
        - Address in sjediste.ulica + sjediste.kucni_broj
        - City in sjediste.naziv_naselja
        - County in sjediste.naziv_zupanije
        - Email in email_adrese[0].adresa
        - OIB in potpuni_oib (with leading zeros preserved)
        
        Note: Phone number and postal code are NOT available from this API.
        """
        if not data or not isinstance(data, dict):
            return None
        
        # Extract tvrtka (company name)
        tvrtka = data.get('tvrtka', {}) or {}
        skracena_tvrtka = data.get('skracena_tvrtka', {}) or {}
        
        # Extract sjediste (registered address)
        sjediste = data.get('sjediste', {}) or {}
        
        # Build full address from ulica + kucni_broj
        ulica = sjediste.get('ulica', '')
        kucni_broj = sjediste.get('kucni_broj', '')
        if ulica:
            address = f"{ulica} {kucni_broj}".strip() if kucni_broj else ulica
        else:
            address = None
        
        # Extract email from email_adrese array
        email = None
        email_adrese = data.get('email_adrese', [])
        if email_adrese and len(email_adrese) > 0:
            email = email_adrese[0].get('adresa')
        
        # Extract capital (latest entry from temeljni_kapitali)
        capital = None
        temeljni_kapitali = data.get('temeljni_kapitali', [])
        if temeljni_kapitali:
            latest = temeljni_kapitali[-1]
            capital = str(latest.get('iznos', '')) if latest.get('iznos') else None
        
        # Extract legal form
        pravni_oblik = data.get('pravni_oblik', {}) or {}
        legal_form_id = pravni_oblik.get('vrsta_pravnog_oblika_id')
        legal_form = str(legal_form_id) if legal_form_id else None
        
        # Use potpuni_oib to preserve leading zeros, fallback to zero-padded oib
        oib_value = data.get('potpuni_oib')
        if not oib_value:
            raw_oib = data.get('oib')
            oib_value = str(raw_oib).zfill(11) if raw_oib else None
        
        # Use potpuni_mbs or mbs
        mbs_value = data.get('potpuni_mbs') or str(data.get('mbs', '')) or None
        
        # County from sjediste.naziv_zupanije
        county = sjediste.get('naziv_zupanije')
        if county:
            county = county.upper()
        
        return CompanyData(
            oib=oib_value,
            mbs=mbs_value,
            name=clean_company_name(tvrtka.get('ime')),
            short_name=clean_company_name(skracena_tvrtka.get('ime')),
            address=address,
            city=sjediste.get('naziv_naselja'),
            postal_code=None,  # Not available in API
            county=county,
            legal_form=legal_form,
            main_activity=None,  # Would need to parse predmeti_poslovanja
            registration_date=None,
            capital=capital,
            status=str(data.get('status', '')) if data.get('status') else None,
            phone=None,  # Not available in API
            email=email,
            raw_data=data
        )
    
    def search_by_mbs(self, mbs: str) -> Optional[CompanyData]:
        """
        Search for a company by MBS (Matični broj subjekta).
        
        Args:
            mbs: Company registration number
            
        Returns:
            CompanyData object or None if not found
        """
        if not mbs:
            raise CourtRegistryError("MBS je obavezan.")
        
        # Check cache first
        cache_key = f"court_registry_mbs_{mbs}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Use path parameter: /subjekti/{mbs}
            response = self._make_request(
                f'/subjekti/{mbs}'
            )
            
            if response:
                # If the API returns a list, take the first result
                if isinstance(response, list):
                    if not response:
                        return None
                    response = response[0]
                
                company_data = self._parse_company_response(response)
                if company_data:
                    cache.set(cache_key, company_data, self.CACHE_TIMEOUT)
                return company_data
                
        except CourtRegistryError:
            raise
        except Exception as e:
            logger.error(f"Error searching by MBS {mbs}: {e}")
            raise CourtRegistryError(f"Greška pri pretraživanju: {str(e)}")
        
        return None
    
    def search_by_name(self, name: str, limit: int = 10) -> List[CompanyData]:
        """
        Search for companies by name.
        
        Args:
            name: Company name to search for
            limit: Maximum number of results
            
        Returns:
            List of CompanyData objects
        """
        if not name or len(name) < 3:
            raise CourtRegistryError("Naziv mora sadržavati najmanje 3 znaka.")
        
        try:
            # Use the name search endpoint
            response = self._make_request(
                '/subjekti',
                params={
                    'naziv': name
                }
            )
            
            results = []
            if not response:
                return results

            if isinstance(response, list):
                items = response
            elif isinstance(response, dict):
                # Handle paginated response or single object wrapped in dict
                items = response.get('rezultati') or response.get('subjekti') or [response]
                if not isinstance(items, list):
                    items = [items]
            else:
                items = []
            
            for item in items[:limit]:
                if item:
                    company_data = self._parse_company_response(item)
                    if company_data:
                        results.append(company_data)
            
            return results
            
        except CourtRegistryError:
            raise
        except Exception as e:
            logger.error(f"Error searching by name '{name}': {e}")
            raise CourtRegistryError(f"Greška pri pretraživanju: {str(e)}")
    
    def _parse_company_response(self, data: Dict) -> Optional[CompanyData]:
        """
        Parse API response into CompanyData object.
        
        The court registry API returns data in various formats depending on the endpoint.
        This method handles the common fields.
        """
        if not data or not isinstance(data, dict):
            return None
        
        # Handle nested data structure
        if 'subjekt' in data:
            data = data['subjekt']
            if isinstance(data, list) and data:
                data = data[0]
            
        if not isinstance(data, dict):
            return None
        
        address, city, postal_code, address_data = _extract_address_components(data)
        county = _extract_county(data, address_data)
        phone = _extract_contact_value(data, _PHONE_KEYS, _PHONE_TYPE_HINTS)
        email = _extract_contact_value(data, _EMAIL_KEYS, _EMAIL_TYPE_HINTS)

        oib = _coalesce_value(
            data.get('oib'),
            _find_value_by_keys(data, {'oib'})
        )
        mbs = _coalesce_value(
            data.get('mbs'),
            data.get('maticniBroj'),
            data.get('maticni_broj'),
            _find_value_by_keys(data, {'mbs', 'maticniBroj', 'maticni_broj'})
        )
        name = _coalesce_value(
            data.get('naziv'),
            data.get('tvrtka'),
            data.get('ime'),
            _find_value_by_keys(data, {'naziv', 'tvrtka', 'ime', 'puniNaziv', 'nazivTvrtke', 'nazivPravneOsobe'})
        )
        short_name = _coalesce_value(
            data.get('skraceniNaziv'),
            data.get('skracenoIme'),
            _find_value_by_keys(data, {'skraceniNaziv', 'skracenoIme', 'kraciNaziv', 'nazivSkraceni'})
        )
        legal_form = _coalesce_value(
            data.get('pravniOblik'),
            data.get('oblikPravneOsobe'),
            _find_value_by_keys(data, {'pravniOblik', 'oblikPravneOsobe'})
        )
        main_activity = _coalesce_value(
            data.get('glavnaDjelatnost'),
            data.get('nkd'),
            _find_value_by_keys(data, {'glavnaDjelatnost', 'nkd', 'djelatnost'})
        )
        registration_date = _coalesce_value(
            data.get('datumOsnivanja'),
            data.get('datumUpisa'),
            _find_value_by_keys(data, {'datumOsnivanja', 'datumUpisa', 'datumUpisaURegistar'})
        )
        status = _coalesce_value(
            data.get('status'),
            data.get('stanje'),
            _find_value_by_keys(data, {'status', 'stanje'})
        )
        capital = _coalesce_value(
            data.get('temeljniKapital'),
            _find_value_by_keys(data, {'temeljniKapital', 'kapital'})
        )
        
        return CompanyData(
            oib=str(oib) if oib else None,
            mbs=str(mbs) if mbs else None,
            name=clean_company_name(name),
            short_name=clean_company_name(short_name),
            address=address,
            city=city,
            postal_code=str(postal_code) if postal_code else None,
            county=county,
            legal_form=legal_form,
            main_activity=main_activity,
            registration_date=registration_date,
            capital=str(capital) if capital else None,
            status=status,
            phone=phone,
            email=email,
            raw_data=data
        )


class CourtRegistryError(Exception):
    """Exception raised for court registry API errors."""
    pass


def get_court_registry_client() -> CourtRegistryClient:
    """
    Get a configured CourtRegistryClient instance using stored credentials.
    
    Returns:
        CourtRegistryClient instance with valid configuration
        
    Raises:
        CourtRegistryError: If no active configuration exists or credentials are missing
    """
    try:
        from arvelloapp.models import CourtRegistryConfig
        
        config = CourtRegistryConfig.objects.filter(is_active=True).first()
        if not config:
            raise CourtRegistryError(
                "Konfiguracija Sudskog registra nije pronađena. "
                "Molimo postavite API podatke u Administracija > Sudski registar."
            )
        
        # Validate that credentials are present
        if not config.client_id or not config.client_secret:
            raise CourtRegistryError(
                "Client ID ili Client Secret nisu postavljeni. "
                "Molimo unesite ispravne API podatke u Administracija > Sudski registar."
            )
        
        return CourtRegistryClient(
            client_id=config.client_id,
            client_secret=config.client_secret,
            use_sandbox=config.use_sandbox,
            config=config  # Pass config for token caching
        )
        
    except CourtRegistryError:
        raise
    except Exception as e:
        logger.error(f"Error getting court registry client: {e}")
        raise CourtRegistryError(
            "Došlo je do greške pri učitavanju konfiguracije Sudskog registra. "
            "Molimo provjerite postavke ili kontaktirajte podršku."
        )


def fetch_company_data_by_oib(oib: str, entity_type: str = 'client') -> Dict[str, Any]:
    """
    Convenience function to fetch company data by OIB.
    
    Args:
        oib: 11-digit OIB number
        entity_type: Type of entity ('client' or 'supplier') - affects field names in response
        
    Returns:
        Dictionary with company data suitable for form population
        
    Raises:
        CourtRegistryError: If configuration is missing or API call fails
    """
    client = get_court_registry_client()  # Will raise CourtRegistryError if not configured
    
    company = client.search_by_oib(oib)
    if not company:
        raise CourtRegistryError("Subjekt s navedenim OIB-om nije pronađen u registru.")
    
    # Map county to PROVINCES choice
    county_mapping = _get_county_mapping()
    province = county_mapping.get(company.county.upper() if company.county else '', '')
    
    # Base data common to both entity types
    base_data = {
        'addressLine1': company.address or '',
        'town': company.city or '',
        'postalCode': company.postal_code or '',
        'province': province,
        'phoneNumber': company.phone or '',
        'emailAddress': company.email or '',
        'OIB': company.oib or oib,
        'mbs': company.mbs or '',
        'legalForm': company.legal_form or '',
        'mainActivity': company.main_activity or '',
        'registrationDate': company.registration_date or '',
        'capital': company.capital or '',
        'status': company.status or '',
    }
    
    if entity_type == 'supplier':
        # Return data with supplier-specific field names
        return {
            **base_data,
            'supplierName': company.name or '',
            'businessType': 'Pravna osoba',  # Companies from registry are legal entities
        }
    else:
        # Return data with client-specific field names (default)
        return {
            **base_data,
            'clientName': company.name or '',
            'clientType': 'Pravna osoba',  # Companies from registry are legal entities
            'VATID': f'HR{company.oib}' if company.oib else '',
        }


def search_companies_by_name(name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Convenience function to search companies by name.
    
    Args:
        name: Company name to search for
        limit: Maximum number of results
        
    Returns:
        List of dictionaries with company data
        
    Raises:
        CourtRegistryError: If configuration is missing or API call fails
    """
    client = get_court_registry_client()  # Will raise CourtRegistryError if not configured
    
    companies = client.search_by_name(name, limit)
    
    return [
        {
            'oib': company.oib or '',
            'mbs': company.mbs or '',
            'name': company.name or '',
            'address': company.address or '',
            'city': company.city or '',
            'postalCode': company.postal_code or '',
        }
        for company in companies
    ]


def _get_county_mapping() -> Dict[str, str]:
    """Get mapping from county names to PROVINCES choices."""
    return {
        'ZAGREBAČKA': 'ZAGREBAČKA ŽUPANIJA',
        'ZAGREBAČKA ŽUPANIJA': 'ZAGREBAČKA ŽUPANIJA',
        'KRAPINSKO-ZAGORSKA': 'KRAPINSKO-ZAGORSKA ŽUPANIJA',
        'KRAPINSKO-ZAGORSKA ŽUPANIJA': 'KRAPINSKO-ZAGORSKA ŽUPANIJA',
        'SISAČKO-MOSLAVAČKA': 'SISAČKO-MOSLAVAČKA ŽUPANIJA',
        'SISAČKO-MOSLAVAČKA ŽUPANIJA': 'SISAČKO-MOSLAVAČKA ŽUPANIJA',
        'KARLOVAČKA': 'KARLOVAČKA ŽUPANIJA',
        'KARLOVAČKA ŽUPANIJA': 'KARLOVAČKA ŽUPANIJA',
        'VARAŽDINSKA': 'VARAŽDINSKA ŽUPANIJA',
        'VARAŽDINSKA ŽUPANIJA': 'VARAŽDINSKA ŽUPANIJA',
        'KOPRIVNIČKO-KRIŽEVAČKA': 'KOPRIVNIČKO-KRIŽEVAČKA ŽUPANIJA',
        'KOPRIVNIČKO-KRIŽEVAČKA ŽUPANIJA': 'KOPRIVNIČKO-KRIŽEVAČKA ŽUPANIJA',
        'BJELOVARSKO-BILOGORSKA': 'BJELOVARSKO-BILOGORSKA ŽUPANIJA',
        'BJELOVARSKO-BILOGORSKA ŽUPANIJA': 'BJELOVARSKO-BILOGORSKA ŽUPANIJA',
        'PRIMORSKO-GORANSKA': 'PRIMORSKO-GORANSKA ŽUPANIJA',
        'PRIMORSKO-GORANSKA ŽUPANIJA': 'PRIMORSKO-GORANSKA ŽUPANIJA',
        'LIČKO-SENJSKA': 'LIČKO-SENJSKA ŽUPANIJA',
        'LIČKO-SENJSKA ŽUPANIJA': 'LIČKO-SENJSKA ŽUPANIJA',
        'VIROVITIČKO-PODRAVSKA': 'VIROVITIČKO-PODRAVSKA ŽUPANIJA',
        'VIROVITIČKO-PODRAVSKA ŽUPANIJA': 'VIROVITIČKO-PODRAVSKA ŽUPANIJA',
        'POŽEŠKO-SLAVONSKA': 'POŽEŠKO-SLAVONSKA ŽUPANIJA',
        'POŽEŠKO-SLAVONSKA ŽUPANIJA': 'POŽEŠKO-SLAVONSKA ŽUPANIJA',
        'BRODSKO-POSAVSKA': 'BRODSKO-POSAVSKA ŽUPANIJA',
        'BRODSKO-POSAVSKA ŽUPANIJA': 'BRODSKO-POSAVSKA ŽUPANIJA',
        'ZADARSKA': 'ZADARSKA ŽUPANIJA',
        'ZADARSKA ŽUPANIJA': 'ZADARSKA ŽUPANIJA',
        'OSJEČKO-BARANJSKA': 'OSJEČKO-BARANJSKA ŽUPANIJA',
        'OSJEČKO-BARANJSKA ŽUPANIJA': 'OSJEČKO-BARANJSKA ŽUPANIJA',
        'ŠIBENSKO-KNINSKA': 'ŠIBENSKO-KNINSKA ŽUPANIJA',
        'ŠIBENSKO-KNINSKA ŽUPANIJA': 'ŠIBENSKO-KNINSKA ŽUPANIJA',
        'VUKOVARSKO-SRIJEMSKA': 'VUKOVARSKO-SRIJEMSKA ŽUPANIJA',
        'VUKOVARSKO-SRIJEMSKA ŽUPANIJA': 'VUKOVARSKO-SRIJEMSKA ŽUPANIJA',
        'SPLITSKO-DALMATINSKA': 'SPLITSKO-DALMATINSKA ŽUPANIJA',
        'SPLITSKO-DALMATINSKA ŽUPANIJA': 'SPLITSKO-DALMATINSKA ŽUPANIJA',
        'ISTARSKA': 'ISTARSKA ŽUPANIJA',
        'ISTARSKA ŽUPANIJA': 'ISTARSKA ŽUPANIJA',
        'DUBROVAČKO-NERETVANSKA': 'DUBROVAČKO-NERETVANSKA ŽUPANIJA',
        'DUBROVAČKO-NERETVANSKA ŽUPANIJA': 'DUBROVAČKO-NERETVANSKA ŽUPANIJA',
        'MEĐIMURSKA': 'MEĐIMURSKA ŽUPANIJA',
        'MEĐIMURSKA ŽUPANIJA': 'MEĐIMURSKA ŽUPANIJA',
        'GRAD ZAGREB': 'GRAD ZAGREB',
        'ZAGREB': 'GRAD ZAGREB',
    }
