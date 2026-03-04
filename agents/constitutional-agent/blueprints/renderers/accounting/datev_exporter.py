"""
DATEV Exporter
===============
Exports invoices to DATEV EXTF format for German accounting software.

Supports:
- SKR03 (Standardkontenrahmen 03) - Commerce/Services
- SKR04 (Standardkontenrahmen 04) - Industry

DATEV EXTF format specification:
- Header row with metadata
- Semicolon-separated values
- German number format (comma as decimal)
- UTF-8 encoding

Wave3: Full DATEV export support.
"""

from datetime import datetime
from typing import Any, Dict, List


class DATEVExporter:
    """Exporter for DATEV EXTF format."""

    # SKR03 account mapping
    SKR03_ACCOUNTS = {
        # Assets / Aktiva
        "bank": "1200",
        "cash": "1000",
        "accounts_receivable": "1400",  # Forderungen LuL
        "accounts_payable": "1600",  # Verbindlichkeiten LuL

        # Revenue / Umsatzerlose
        "revenue_19": "8400",  # Erlose 19% USt
        "revenue_7": "8300",  # Erlose 7% USt
        "revenue_0": "8100",  # Steuerfreie Inlandsumsatze

        # Expenses / Aufwendungen
        "goods_purchase": "3400",  # Wareneingang 19%
        "goods_purchase_7": "3300",  # Wareneingang 7%

        # Tax accounts / Steuerkonten
        "vat_19": "1776",  # Umsatzsteuer 19%
        "vat_7": "1771",  # Umsatzsteuer 7%
        "input_vat_19": "1576",  # Vorsteuer 19%
        "input_vat_7": "1571",  # Vorsteuer 7%
    }

    # SKR04 account mapping
    SKR04_ACCOUNTS = {
        # Assets / Aktiva
        "bank": "1800",
        "cash": "1600",
        "accounts_receivable": "1200",  # Forderungen LuL
        "accounts_payable": "3300",  # Verbindlichkeiten LuL

        # Revenue / Umsatzerlose
        "revenue_19": "4400",  # Erlose 19% USt
        "revenue_7": "4300",  # Erlose 7% USt
        "revenue_0": "4100",  # Steuerfreie Inlandsumsatze

        # Expenses / Aufwendungen
        "goods_purchase": "5400",  # Wareneingang 19%
        "goods_purchase_7": "5300",  # Wareneingang 7%

        # Tax accounts / Steuerkonten
        "vat_19": "3806",  # Umsatzsteuer 19%
        "vat_7": "3801",  # Umsatzsteuer 7%
        "input_vat_19": "1576",  # Vorsteuer 19%
        "input_vat_7": "1571",  # Vorsteuer 7%
    }

    # DATEV BU-Schlussel (tax codes)
    BU_CODES = {
        0.19: "3",  # 19% USt
        0.07: "2",  # 7% USt
        0.0: "0",  # No tax
    }

    def __init__(self, chart: str = "SKR03"):
        """
        Initialize exporter.

        Args:
            chart: Account chart (SKR03 or SKR04)
        """
        self.chart = chart.upper()
        self.accounts = self.SKR03_ACCOUNTS if self.chart == "SKR03" else self.SKR04_ACCOUNTS

    def get_accounts(self) -> Dict[str, str]:
        """Return the account mapping for the selected chart."""
        return self.accounts.copy()

    def export(self, invoices: List[Dict[str, Any]], period: str) -> str:
        """
        Export invoices to DATEV EXTF format.

        Args:
            invoices: List of invoice dictionaries
            period: Fiscal period (YYYY-MM)

        Returns:
            DATEV CSV content
        """
        lines = []

        # EXTF Header (line 1)
        header = self._build_header(period)
        lines.append(header)

        # Column header (line 2)
        columns = self._build_columns()
        lines.append(columns)

        # Booking lines
        for invoice in invoices:
            booking_line = self._build_booking_line(invoice)
            if booking_line:
                lines.append(booking_line)

        return "\n".join(lines)

    def _build_header(self, period: str) -> str:
        """Build EXTF header line."""
        # Parse period
        year, month = period.split("-")

        # EXTF header fields
        fields = [
            "EXTF",  # Format identifier
            "700",  # Version
            "21",  # Kategorie: Buchungsstapel
            "Buchungsstapel",  # Description
            "12",  # Version of category
            str(datetime.now().strftime("%Y%m%d%H%M%S%f")[:14]),  # Created timestamp
            "",  # Reserved
            "",  # Reserved
            "RE",  # Type: Rechnungseingangsbuch
            "",  # Reserved
            "",  # Reserved
            f"{year}0101",  # WJ-Begin (fiscal year start)
            self.chart[-2:],  # SKR number
            f"{period.replace('-', '')}01",  # Period start
            f"{period.replace('-', '')}{self._days_in_month(int(year), int(month)):02d}",  # Period end
            "",  # Reserved
            "",  # Reserved
            "",  # Reserved
            "EUR",  # Currency
            "",  # Reserved
            "",  # Reserved
            "",  # Reserved
            "",  # Reserved
            "",  # Reserved
            "",  # Reserved
            "",  # Reserved
        ]

        return ";".join(fields)

    def _build_columns(self) -> str:
        """Build column header line."""
        columns = [
            "Umsatz (ohne Soll/Haben-Kz)",
            "Soll/Haben-Kennzeichen",
            "WKZ Umsatz",
            "Kurs",
            "Basis-Umsatz",
            "WKZ Basis-Umsatz",
            "Konto",
            "Gegenkonto (ohne BU-Schlussel)",
            "BU-Schlussel",
            "Belegdatum",
            "Belegfeld 1",
            "Belegfeld 2",
            "Skonto",
            "Buchungstext",
            "Postensperre",
            "Diverse Adressnummer",
            "Geschaftspartnerbank",
            "Sachverhalt",
            "Zinssperre",
            "Beleglink",
            "Beleginfo - Art 1",
            "Beleginfo - Inhalt 1",
            "Beleginfo - Art 2",
            "Beleginfo - Inhalt 2",
            "Beleginfo - Art 3",
            "Beleginfo - Inhalt 3",
        ]

        return ";".join(columns)

    def _build_booking_line(self, invoice: Dict[str, Any]) -> str:
        """Build booking line for an invoice."""
        doc_type = invoice.get("doc_type", "eingangsrechnung")
        gross = invoice.get("gross_amount", 0)
        vat_rate = invoice.get("vat_rate", 0.19)
        invoice_date = invoice.get("invoice_date", "")
        invoice_number = invoice.get("invoice_number", "")
        supplier_name = invoice.get("supplier_name", "")

        # Determine accounts and direction based on document type
        if doc_type == "eingangsrechnung":
            # Incoming invoice: Debit expense, Credit payables
            soll_haben = "S"  # Soll (Debit)
            konto = self.accounts["goods_purchase"]
            gegenkonto = self.accounts["accounts_payable"]
            text = f"Eingangsrechnung {supplier_name}"
        elif doc_type == "ausgangsrechnung":
            # Outgoing invoice: Debit receivables, Credit revenue
            soll_haben = "H"  # Haben (Credit)
            konto = self.accounts["revenue_19"]
            gegenkonto = self.accounts["accounts_receivable"]
            text = f"Ausgangsrechnung {invoice_number}"
        elif doc_type == "gutschrift":
            # Credit note: reverse of invoice
            soll_haben = "H"
            konto = self.accounts["accounts_payable"]
            gegenkonto = self.accounts["goods_purchase"]
            text = f"Gutschrift {supplier_name}"
        else:
            return ""

        # Format amount (German: comma as decimal)
        amount_str = f"{abs(gross):.2f}".replace(".", ",")

        # Format date (DDMM)
        if invoice_date:
            try:
                dt = datetime.fromisoformat(invoice_date)
                date_str = dt.strftime("%d%m")
            except ValueError:
                date_str = ""
        else:
            date_str = ""

        # Get BU code
        bu_code = self.BU_CODES.get(vat_rate, "3")

        # Build line fields
        fields = [
            amount_str,  # Umsatz
            soll_haben,  # S/H
            "EUR",  # WKZ
            "",  # Kurs
            "",  # Basis-Umsatz
            "",  # WKZ Basis
            konto,  # Konto
            gegenkonto,  # Gegenkonto
            bu_code,  # BU-Schlussel
            date_str,  # Belegdatum
            invoice_number[:12] if invoice_number else "",  # Belegfeld 1 (max 12)
            "",  # Belegfeld 2
            "",  # Skonto
            text[:60],  # Buchungstext (max 60)
            "",  # Postensperre
            "",  # Diverse Adressnummer
            "",  # Geschaftspartnerbank
            "",  # Sachverhalt
            "",  # Zinssperre
            "",  # Beleglink
            "Lieferant",  # Beleginfo Art 1
            supplier_name[:50] if supplier_name else "",  # Beleginfo Inhalt 1
            "",  # Beleginfo Art 2
            "",  # Beleginfo Inhalt 2
            "",  # Beleginfo Art 3
            "",  # Beleginfo Inhalt 3
        ]

        return ";".join(str(f) for f in fields)

    def _days_in_month(self, year: int, month: int) -> int:
        """Return number of days in a month."""
        if month in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        elif month in [4, 6, 9, 11]:
            return 30
        elif month == 2:
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                return 29
            return 28
        return 30
