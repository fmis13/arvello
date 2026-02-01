from lxml import etree


def validate_xml(xml_bytes: bytes, xsd_path: str) -> bool:
    """Validate xml_bytes against XSD file at xsd_path. Returns True if valid, False otherwise."""
    with open(xsd_path, 'rb') as f:
        schema_doc = etree.parse(f)
        schema = etree.XMLSchema(schema_doc)
        doc = etree.fromstring(xml_bytes)
        return schema.validate(doc)
