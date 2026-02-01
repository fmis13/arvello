from typing import Any, Dict


class ProviderAdapter:
    """Base adapter interface for fiscal providers."""

    def __init__(self, mode: str = "production"):
        self.mode = mode

    def prepare_payload(self, document: Any) -> Dict:
        """Map domain document to provider payload."""
        raise NotImplementedError()

    def sign_payload(self, payload: Dict) -> Any:
        """Sign payload according to provider requirements."""
        raise NotImplementedError()

    def send(self, signed_payload: Any) -> Any:
        """Send signed payload to provider endpoint and return raw response."""
        raise NotImplementedError()

    def parse_response(self, raw_response: Any) -> Dict:
        """Parse provider response into structured dict."""
        raise NotImplementedError()

    def fiscalize(self, document: Any) -> Dict:
        """High-level fiscalization method that orchestrates the process."""
        payload = self.prepare_payload(document)
        signed = self.sign_payload(payload)
        raw_response = self.send(signed)
        parsed = self.parse_response(raw_response)
        return parsed

    def health_check(self) -> bool:
        """Optional health check for provider connectivity."""
        return True

    def test_connection(self) -> dict:
        """Test connection to fiscal provider."""
        try:
            health = self.health_check()
            return {'success': health, 'message': 'Connection test successful' if health else 'Connection test failed'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
