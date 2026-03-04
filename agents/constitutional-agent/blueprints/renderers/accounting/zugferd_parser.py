"""
ZUGFeRD Parser
===============
Parses ZUGFeRD PDF invoices with embedded XML.

ZUGFeRD combines PDF/A-3 with embedded XML (CrossIndustryInvoice).
Namespace: urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100

Wave3: Detection and extraction using stdlib only.
       No PyPDF2 or other external dependencies.
"""

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class ZUGFeRDParser:
    """Parser for ZUGFeRD PDF+XML invoices."""

    # CrossIndustryInvoice namespaces
    NAMESPACES = {
        "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
        "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
        "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
    }

    def __init__(self, content: bytes):
        """
        Initialize with PDF content.

        Args:
            content: Raw PDF bytes
        """
        self.content = content
        self.xml_content: Optional[str] = None
        self.root: Optional[ET.Element] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.extracted_data: Dict[str, Any] = {}

    def is_zugferd(self) -> bool:
        """
        Detect if this is a ZUGFeRD PDF.

        Looks for CrossIndustryInvoice in the PDF stream.
        """
        try:
            # Check PDF magic
            if not self.content.startswith(b"%PDF"):
                return False

            # Look for ZUGFeRD/Factur-X markers
            markers = [
                b"CrossIndustryInvoice",
                b"ZUGFeRD",
                b"Factur-X",
                b"factur-x.xml",
                b"zugferd-invoice.xml",
                b"urn:un:unece:uncefact",
            ]

            for marker in markers:
                if marker in self.content:
                    return True

            return False
        except Exception:
            return False

    def extract_xml(self) -> Optional[str]:
        """
        Extract embedded XML from PDF.

        Wave3: Uses regex-based extraction without PyPDF2.
        """
        try:
            # Method 1: Look for XML declaration followed by CrossIndustryInvoice
            patterns = [
                # Standard XML with CrossIndustryInvoice
                rb'<\?xml[^>]*\?>.*?<rsm:CrossIndustryInvoice[^>]*>.*?</rsm:CrossIndustryInvoice>',
                rb'<\?xml[^>]*\?>.*?<CrossIndustryInvoice[^>]*>.*?</CrossIndustryInvoice>',
                # Without namespace prefix
                rb'<CrossIndustryInvoice[^>]*>.*?</CrossIndustryInvoice>',
            ]

            for pattern in patterns:
                match = re.search(pattern, self.content, re.DOTALL)
                if match:
                    self.xml_content = match.group(0).decode("utf-8", errors="replace")
                    return self.xml_content

            # Method 2: Look for embedded files marker
            # PDF embedded files use /EmbeddedFiles dictionary
            if b"/EmbeddedFiles" in self.content or b"/AF" in self.content:
                # Find stream content that looks like XML
                stream_pattern = rb'stream\r?\n(.*?)\r?\nendstream'
                streams = re.findall(stream_pattern, self.content, re.DOTALL)

                for stream in streams:
                    # Check if stream looks like XML invoice
                    if b"CrossIndustryInvoice" in stream:
                        try:
                            xml_start = stream.find(b"<?xml")
                            if xml_start == -1:
                                xml_start = stream.find(b"<rsm:")
                            if xml_start == -1:
                                xml_start = stream.find(b"<CrossIndustryInvoice")

                            if xml_start >= 0:
                                self.xml_content = stream[xml_start:].decode("utf-8", errors="replace")
                                return self.xml_content
                        except Exception:
                            continue

            # Method 3: Decompress streams (basic FlateDecode support)
            try:
                import zlib

                # Find compressed streams
                for match in re.finditer(rb'/FlateDecode.*?stream\r?\n(.*?)\r?\nendstream', self.content, re.DOTALL):
                    try:
                        decompressed = zlib.decompress(match.group(1))
                        if b"CrossIndustryInvoice" in decompressed:
                            xml_start = decompressed.find(b"<?xml")
                            if xml_start == -1:
                                xml_start = decompressed.find(b"<rsm:")
                            if xml_start >= 0:
                                self.xml_content = decompressed[xml_start:].decode("utf-8", errors="replace")
                                return self.xml_content
                    except zlib.error:
                        continue
            except ImportError:
                pass

            self.warnings.append("Could not extract embedded XML from PDF")
            return None

        except Exception as e:
            self.errors.append(f"XML extraction failed: {str(e)}")
            return None

    def parse(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Parse ZUGFeRD invoice.

        Returns:
            Tuple of (success, extracted_data)
        """
        if not self.is_zugferd():
            # Not ZUGFeRD - return for OCR fallback
            return False, {
                "format": "pdf",
                "zugferd": False,
                "ocr_required": True,
                "errors": ["Not a ZUGFeRD PDF, OCR required"],
            }

        # Extract embedded XML
        xml = self.extract_xml()
        if not xml:
            return False, {
                "format": "pdf",
                "zugferd": True,
                "ocr_required": True,
                "errors": ["ZUGFeRD detected but XML extraction failed"],
            }

        # Parse XML
        try:
            self.root = ET.fromstring(xml)
        except ET.ParseError as e:
            self.errors.append(f"XML parse error: {str(e)}")
            return False, {
                "format": "zugferd",
                "errors": self.errors,
            }

        # Extract invoice data
        self._extract_invoice_number()
        self._extract_dates()
        self._extract_parties()
        self._extract_amounts()

        return True, {
            "format": "zugferd",
            "valid": len(self.errors) == 0,
            "data": self.extracted_data,
            "errors": self.errors,
            "warnings": self.warnings,
            "raw_xml": xml,
        }

    def _find_text(self, element: ET.Element, path: str) -> Optional[str]:
        """Find text in element using path."""
        # Try with namespaces
        for ns_prefix, ns_uri in self.NAMESPACES.items():
            try:
                parts = path.split("/")
                ns_path = "/".join(f"{{{ns_uri}}}{p}" for p in parts)
                elem = element.find(ns_path)
                if elem is not None and elem.text:
                    return elem.text.strip()
            except Exception:
                continue

        # Fallback: search by local name
        search_name = path.split("/")[-1]
        for child in element.iter():
            local_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if local_name == search_name and child.text:
                return child.text.strip()

        return None

    def _extract_invoice_number(self):
        """Extract invoice number."""
        if self.root is None:
            return

        # Look for ExchangedDocument/ID
        for elem in self.root.iter():
            local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if local_name == "ExchangedDocument":
                for child in elem.iter():
                    child_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if child_name == "ID" and child.text:
                        self.extracted_data["invoice_number"] = child.text.strip()
                        return

    def _extract_dates(self):
        """Extract invoice and due dates."""
        if self.root is None:
            return

        for elem in self.root.iter():
            local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

            if local_name == "IssueDateTime":
                for child in elem.iter():
                    child_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if child_name == "DateTimeString" and child.text:
                        date_str = child.text.strip()
                        self._parse_date(date_str)
                        return

    def _parse_date(self, date_str: str):
        """Parse date string and set invoice_date and period."""
        formats = [
            ("%Y%m%d", None),
            ("%Y-%m-%d", None),
            ("%d.%m.%Y", None),
        ]

        for fmt, _ in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                self.extracted_data["invoice_date"] = dt.strftime("%Y-%m-%d")
                self.extracted_data["period"] = dt.strftime("%Y-%m")
                return
            except ValueError:
                continue

    def _extract_parties(self):
        """Extract seller and buyer information."""
        if self.root is None:
            return

        for elem in self.root.iter():
            local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

            if local_name == "SellerTradeParty":
                self._extract_party(elem, "supplier")

            elif local_name == "BuyerTradeParty":
                self._extract_party(elem, "recipient")

    def _extract_party(self, party_elem: ET.Element, prefix: str):
        """Extract party details."""
        for child in party_elem.iter():
            local_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag

            if local_name == "Name" and child.text:
                self.extracted_data[f"{prefix}_name"] = child.text.strip()

            elif local_name == "ID" and child.text:
                text = child.text.strip()
                # Check schemeID for VAT
                scheme = child.get("schemeID", "")
                if scheme == "VA" or text.startswith("DE"):
                    self.extracted_data[f"{prefix}_vat"] = text

    def _extract_amounts(self):
        """Extract monetary amounts."""
        if self.root is None:
            return

        for elem in self.root.iter():
            local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

            if local_name == "SpecifiedTradeSettlementHeaderMonetarySummation":
                self._extract_monetary_summary(elem)

            elif local_name == "ApplicableTradeTax":
                self._extract_tax_info(elem)

    def _extract_monetary_summary(self, summary_elem: ET.Element):
        """Extract monetary summary amounts."""
        for child in summary_elem.iter():
            local_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag

            if local_name == "TaxBasisTotalAmount" and child.text:
                self.extracted_data["net_amount"] = float(child.text)

            elif local_name == "TaxTotalAmount" and child.text:
                self.extracted_data["vat_amount"] = float(child.text)

            elif local_name == "GrandTotalAmount" and child.text:
                self.extracted_data["gross_amount"] = float(child.text)

    def _extract_tax_info(self, tax_elem: ET.Element):
        """Extract tax rate information."""
        for child in tax_elem.iter():
            local_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag

            if local_name == "RateApplicablePercent" and child.text:
                rate = float(child.text)
                if rate > 1:
                    rate = rate / 100
                self.extracted_data["vat_rate"] = rate
                return
