"""
XRechnung Validator
====================
Validates and parses XRechnung XML (UBL 2.1 format).

XRechnung is the German e-invoicing standard based on EN 16931.
Uses namespace: urn:oasis:names:specification:ubl:schema:xsd:Invoice-2

Wave3: Validation using stdlib xml.etree only (no lxml).
"""

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class XRechnungValidator:
    """Validator for XRechnung XML invoices."""

    # UBL 2.1 namespaces
    NAMESPACES = {
        "ubl": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    }

    # Required fields for GoBD compliance
    REQUIRED_FIELDS = [
        "invoice_number",
        "invoice_date",
        "supplier_name",
        "net_amount",
        "vat_amount",
        "gross_amount",
    ]

    def __init__(self, xml_content: str):
        """Initialize with XML content."""
        self.xml_content = xml_content
        self.root = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.extracted_data: Dict[str, Any] = {}

    def parse(self) -> bool:
        """Parse the XML content."""
        try:
            self.root = ET.fromstring(self.xml_content)
            return True
        except ET.ParseError as e:
            self.errors.append(f"XML parse error: {str(e)}")
            return False

    def validate(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate XRechnung and extract data.

        Returns:
            Tuple of (is_valid, extracted_data)
        """
        if not self.parse():
            return False, {"errors": self.errors}

        # Check if it's UBL Invoice
        if not self._is_ubl_invoice():
            self.errors.append("Not a valid UBL Invoice document")
            return False, {"errors": self.errors}

        # Extract all fields
        self._extract_invoice_number()
        self._extract_invoice_date()
        self._extract_supplier()
        self._extract_recipient()
        self._extract_amounts()
        self._extract_vat()

        # Validate required fields
        for field in self.REQUIRED_FIELDS:
            if not self.extracted_data.get(field):
                self.errors.append(f"Missing required field: {field}")

        # Validate arithmetic (C4: netto + IVA = gross, tolerance 0.02)
        net = self.extracted_data.get("net_amount", 0.0)
        vat = self.extracted_data.get("vat_amount", 0.0)
        gross = self.extracted_data.get("gross_amount", 0.0)

        if net and vat and gross:
            calculated = net + vat
            if abs(calculated - gross) > 0.02:
                self.errors.append(
                    f"Arithmetic error: {net} + {vat} = {calculated}, but gross is {gross}"
                )

        is_valid = len(self.errors) == 0

        result = {
            "valid": is_valid,
            "format": "xrechnung",
            "data": self.extracted_data,
            "errors": self.errors,
            "warnings": self.warnings,
            "gobd_compliant": is_valid,
        }

        return is_valid, result

    def _is_ubl_invoice(self) -> bool:
        """Check if document is a UBL Invoice."""
        if self.root is None:
            return False

        # Check root tag
        tag = self.root.tag
        if "Invoice" in tag:
            return True

        # Check namespace
        for ns_key, ns_uri in self.NAMESPACES.items():
            if ns_uri in tag:
                return True

        return False

    def _find_element(self, path: str, namespaces: Dict[str, str] = None) -> Optional[ET.Element]:
        """Find element with namespace handling."""
        if self.root is None:
            return None

        ns = namespaces or self.NAMESPACES

        # Try with each namespace prefix
        for prefix, uri in ns.items():
            try:
                # Build namespace-aware path
                parts = path.split("/")
                ns_path = "/".join(f"{{{uri}}}{p}" if not p.startswith("{") else p for p in parts)
                elem = self.root.find(ns_path)
                if elem is not None:
                    return elem
            except Exception:
                continue

        # Fallback: try without namespace
        try:
            return self.root.find(path)
        except Exception:
            return None

    def _get_text(self, path: str, default: str = "") -> str:
        """Get text content of element."""
        elem = self._find_element(path)
        if elem is not None and elem.text:
            return elem.text.strip()

        # Fallback: search by local name
        if self.root is not None:
            for elem in self.root.iter():
                local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                if local_name == path.split("/")[-1]:
                    if elem.text:
                        return elem.text.strip()

        return default

    def _extract_invoice_number(self):
        """Extract invoice number (cbc:ID)."""
        # Try multiple paths
        for path in ["cbc:ID", "ID", "InvoiceNumber"]:
            value = self._get_text(path)
            if value:
                self.extracted_data["invoice_number"] = value
                return

        # Search by tag name
        if self.root is not None:
            for elem in self.root.iter():
                local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                if local_name == "ID" and elem.text:
                    self.extracted_data["invoice_number"] = elem.text.strip()
                    return

    def _extract_invoice_date(self):
        """Extract invoice date (cbc:IssueDate)."""
        for path in ["cbc:IssueDate", "IssueDate", "InvoiceDate"]:
            value = self._get_text(path)
            if value:
                self.extracted_data["invoice_date"] = value
                # Parse to determine period
                try:
                    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    self.extracted_data["period"] = dt.strftime("%Y-%m")
                except ValueError:
                    # Try other formats
                    for fmt in ["%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"]:
                        try:
                            dt = datetime.strptime(value, fmt)
                            self.extracted_data["period"] = dt.strftime("%Y-%m")
                            break
                        except ValueError:
                            continue
                return

    def _extract_supplier(self):
        """Extract supplier information."""
        if self.root is None:
            return

        # Search for supplier party
        for elem in self.root.iter():
            local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

            if local_name in ["AccountingSupplierParty", "SupplierParty"]:
                # Find name
                for child in elem.iter():
                    child_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if child_name == "Name" and child.text:
                        self.extracted_data["supplier_name"] = child.text.strip()
                    elif child_name == "RegistrationName" and child.text:
                        self.extracted_data["supplier_name"] = child.text.strip()
                    elif child_name in ["CompanyID", "ID"] and child.text:
                        # Check if it's a VAT ID
                        if child.text.startswith("DE"):
                            self.extracted_data["supplier_vat"] = child.text.strip()
                return

    def _extract_recipient(self):
        """Extract recipient information."""
        if self.root is None:
            return

        for elem in self.root.iter():
            local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

            if local_name in ["AccountingCustomerParty", "CustomerParty", "BuyerParty"]:
                for child in elem.iter():
                    child_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if child_name == "Name" and child.text:
                        self.extracted_data["recipient_name"] = child.text.strip()
                    elif child_name == "RegistrationName" and child.text:
                        self.extracted_data["recipient_name"] = child.text.strip()
                    elif child_name in ["CompanyID", "ID"] and child.text:
                        if child.text.startswith("DE"):
                            self.extracted_data["recipient_vat"] = child.text.strip()
                return

    def _extract_amounts(self):
        """Extract monetary amounts."""
        if self.root is None:
            return

        for elem in self.root.iter():
            local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

            if local_name == "LegalMonetaryTotal":
                for child in elem.iter():
                    child_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if child_name == "TaxExclusiveAmount" and child.text:
                        self.extracted_data["net_amount"] = float(child.text)
                    elif child_name == "TaxInclusiveAmount" and child.text:
                        self.extracted_data["gross_amount"] = float(child.text)
                    elif child_name == "PayableAmount" and child.text:
                        if "gross_amount" not in self.extracted_data:
                            self.extracted_data["gross_amount"] = float(child.text)
                return

    def _extract_vat(self):
        """Extract VAT information."""
        if self.root is None:
            return

        total_vat = 0.0
        vat_rate = None

        for elem in self.root.iter():
            local_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

            if local_name == "TaxTotal":
                # Get direct child TaxAmount only (not nested in TaxSubtotal)
                for child in elem:
                    child_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if child_name == "TaxAmount" and child.text:
                        total_vat = float(child.text)
                        break  # Take only the first direct TaxAmount

            elif local_name == "TaxSubtotal":
                for child in elem.iter():
                    child_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if child_name == "Percent" and child.text:
                        rate = float(child.text)
                        if rate > 1:
                            rate = rate / 100
                        vat_rate = rate

        if total_vat > 0:
            self.extracted_data["vat_amount"] = total_vat

        if vat_rate is not None:
            self.extracted_data["vat_rate"] = vat_rate
        elif total_vat > 0 and self.extracted_data.get("net_amount"):
            # Calculate rate from amounts
            net = self.extracted_data["net_amount"]
            if net > 0:
                calculated_rate = total_vat / net
                # Round to standard German rates
                if 0.18 <= calculated_rate <= 0.20:
                    self.extracted_data["vat_rate"] = 0.19
                elif 0.06 <= calculated_rate <= 0.08:
                    self.extracted_data["vat_rate"] = 0.07
                else:
                    self.extracted_data["vat_rate"] = round(calculated_rate, 2)

    def get_currency(self) -> str:
        """Extract currency code."""
        if self.root is None:
            return "EUR"

        for elem in self.root.iter():
            # Check currencyID attribute
            currency = elem.get("currencyID")
            if currency:
                return currency

        return "EUR"
