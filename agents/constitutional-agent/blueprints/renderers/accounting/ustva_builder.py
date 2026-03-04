"""
UStVA Builder
==============
Generates UStVA (Umsatzsteuer-Voranmeldung) XML for ELSTER submission.

UStVA is the German VAT advance return, submitted monthly or quarterly
to the Finanzamt (tax authority) via ELSTER.

ELSTER XML namespace: http://www.elster.de/elsterxml/schema/v12

Wave3: XML generation without ELSTER certificate.
       Human downloads and uploads to elster.de manually.
       Wave4 will add Erica integration for direct submission.

CRITICAL (C6): This builder NEVER submits to ELSTER automatically.
               AI prepares. Human approves. ELSTER receives from human.
"""

import hashlib
from datetime import datetime
from typing import Any, Dict, List
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString


class UStVABuilder:
    """Builder for UStVA ELSTER XML."""

    # ELSTER namespace
    ELSTER_NS = "http://www.elster.de/elsterxml/schema/v12"

    # UStVA Kennzahlen (field codes)
    KENNZAHLEN = {
        # Lieferungen und sonstige Leistungen
        "kz_81": "Steuerpflichtige Umsatze 19%",
        "kz_86": "Steuerpflichtige Umsatze 7%",
        "kz_35": "Steuerpflichtige Umsatze andere Steuersatze",
        "kz_36": "Steuer zu KZ 35",

        # Steuerberechnung
        "kz_83": "Steuer zu 19%",
        "kz_86_ust": "Steuer zu 7%",

        # Innergemeinschaftliche Erwerbe
        "kz_89": "Steuerpflichtige innergemeinschaftliche Erwerbe",
        "kz_93": "Steuer zu innergemeinschaftlichen Erwerben",

        # Vorsteuer
        "kz_66": "Vorsteuerbetr\u00e4ge aus Rechnungen",
        "kz_61": "Vorsteuer aus innergemeinschaftlichem Erwerb",
        "kz_62": "Entrichtete Einfuhrumsatzsteuer",
        "kz_67": "Vorsteuer nach Durchschnittss\u00e4tzen",
        "kz_63": "Vorsteuerbetr\u00e4ge Kfz",
        "kz_59": "Vorsteuer aus Rechnungen \u00a7 13b",

        # Berechnung
        "kz_83": "USt 19%",
        "kz_66": "Vorsteuer",
    }

    def __init__(self, company_data: Dict[str, Any] = None):
        """
        Initialize builder.

        Args:
            company_data: Company information (Steuernummer, Name, etc.)
        """
        self.company = company_data or {}

    def build(
        self,
        period: str,
        invoices: List[Dict[str, Any]],
        umsatzsteuer: float = 0.0,
        vorsteuer: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Build UStVA XML.

        Args:
            period: Fiscal period (YYYY-MM)
            invoices: List of invoices for the period
            umsatzsteuer: Total output VAT (from outgoing invoices)
            vorsteuer: Total input VAT (from incoming invoices)

        Returns:
            Dictionary with xml_content, hash, kennzahlen
        """
        # Calculate Kennzahlen from invoices
        kennzahlen = self._calculate_kennzahlen(invoices, umsatzsteuer, vorsteuer)

        # Build XML structure
        xml_content = self._build_xml(period, kennzahlen)

        # Calculate hash
        xml_hash = hashlib.sha256(xml_content.encode()).hexdigest()

        return {
            "period": period,
            "xml_content": xml_content,
            "xml_hash": f"sha256:{xml_hash}",
            "kennzahlen": kennzahlen,
            "zahllast": kennzahlen.get("zahllast", 0.0),
            "generated_at": datetime.now().isoformat(),
            "elster_version": "v12",
            "wave3_note": "XML ready for manual upload to elster.de",
        }

    def _calculate_kennzahlen(
        self,
        invoices: List[Dict[str, Any]],
        umsatzsteuer: float,
        vorsteuer: float,
    ) -> Dict[str, Any]:
        """Calculate Kennzahlen from invoices."""
        # Initialize totals
        umsaetze_19 = 0.0  # KZ 81
        umsaetze_7 = 0.0  # KZ 86
        ust_19 = 0.0  # KZ 83
        ust_7 = 0.0  # KZ 86_ust
        vst_total = 0.0  # KZ 66

        # Process invoices
        for inv in invoices:
            doc_type = inv.get("doc_type", "")
            net = inv.get("net_amount", 0.0)
            vat = inv.get("vat_amount", 0.0)
            rate = inv.get("vat_rate", 0.19)

            if doc_type == "ausgangsrechnung":
                # Outgoing invoice = Umsatz (revenue)
                if abs(rate - 0.19) < 0.01:
                    umsaetze_19 += net
                    ust_19 += vat
                elif abs(rate - 0.07) < 0.01:
                    umsaetze_7 += net
                    ust_7 += vat

            elif doc_type == "eingangsrechnung":
                # Incoming invoice = Vorsteuer (input VAT)
                vst_total += vat

        # Use provided totals if available, otherwise use calculated
        if umsatzsteuer > 0:
            total_ust = umsatzsteuer
        else:
            total_ust = ust_19 + ust_7

        if vorsteuer > 0:
            vst_total = vorsteuer

        # Zahllast = USt - VSt
        zahllast = total_ust - vst_total

        return {
            "kz_81": round(umsaetze_19, 2),  # Bemessungsgrundlage 19%
            "kz_86": round(umsaetze_7, 2),  # Bemessungsgrundlage 7%
            "kz_83": round(ust_19, 2),  # USt 19%
            "kz_86_ust": round(ust_7, 2),  # USt 7%
            "kz_66": round(vst_total, 2),  # Vorsteuer
            "zahllast": round(zahllast, 2),  # Zu zahlen/Erstattung
            "umsatzsteuer_total": round(total_ust, 2),
            "vorsteuer_total": round(vst_total, 2),
        }

    def _build_xml(self, period: str, kennzahlen: Dict[str, Any]) -> str:
        """Build ELSTER-format XML."""
        year, month = period.split("-")

        # Root element with namespace
        root = Element("Elster")
        root.set("xmlns", self.ELSTER_NS)

        # TransferHeader
        transfer_header = SubElement(root, "TransferHeader")
        SubElement(transfer_header, "Version").text = "12"
        SubElement(transfer_header, "Verfahren").text = "ElsterAnmeldung"
        SubElement(transfer_header, "DatenArt").text = "UStVA"
        SubElement(transfer_header, "Vorgang").text = "send-NoSig"

        # DatenTeil
        daten_teil = SubElement(root, "DatenTeil")

        # Nutzdatenblock
        nutzdaten_block = SubElement(daten_teil, "Nutzdatenblock")

        # NutzdatenHeader
        nutzdaten_header = SubElement(nutzdaten_block, "NutzdatenHeader")
        SubElement(nutzdaten_header, "NutzdatenTicket").text = "WAVE3-MANUAL"
        empfaenger = SubElement(nutzdaten_header, "Empfaenger")
        empfaenger.set("id", "F")  # Finanzamt
        empfaenger.text = self.company.get("finanzamt", "0000")

        # Nutzdaten
        nutzdaten = SubElement(nutzdaten_block, "Nutzdaten")

        # Anmeldungssteuern
        anmeldung = SubElement(nutzdaten, "Anmeldungssteuern")
        anmeldung.set("art", "UStVA")
        anmeldung.set("version", "202501")

        # Steuerfall
        steuerfall = SubElement(anmeldung, "Steuerfall")

        # Umsatzsteuervoranmeldung
        ustva = SubElement(steuerfall, "Umsatzsteuervoranmeldung")

        # Jahr und Zeitraum
        SubElement(ustva, "Jahr").text = year
        SubElement(ustva, "Zeitraum").text = f"{int(month):02d}"

        # Company info
        steuernummer = SubElement(ustva, "Steuernummer")
        steuernummer.text = self.company.get("steuernummer", "00/000/00000")

        # Kennzahlen
        kz = SubElement(ustva, "Kz")

        # KZ 81 - Umsatze 19%
        kz81 = SubElement(kz, "Kz81")
        kz81.text = str(int(kennzahlen.get("kz_81", 0)))

        # KZ 83 - USt 19%
        kz83 = SubElement(kz, "Kz83")
        kz83.text = str(int(kennzahlen.get("kz_83", 0) * 100))  # In Cent

        # KZ 86 - Umsatze 7%
        kz86 = SubElement(kz, "Kz86")
        kz86.text = str(int(kennzahlen.get("kz_86", 0)))

        # KZ 66 - Vorsteuer
        kz66 = SubElement(kz, "Kz66")
        kz66.text = str(int(kennzahlen.get("kz_66", 0) * 100))  # In Cent

        # KZ 83 for final calculation (Zahllast)
        # Note: This is simplified; full UStVA has more fields

        # Format XML with indentation
        try:
            xml_str = tostring(root, encoding="unicode")
            dom = parseString(xml_str)
            pretty_xml = dom.toprettyxml(indent="  ", encoding=None)
            # Remove extra blank lines
            lines = [line for line in pretty_xml.split("\n") if line.strip()]
            return "\n".join(lines)
        except Exception:
            return tostring(root, encoding="unicode")

    def preview(
        self,
        period: str,
        invoices: List[Dict[str, Any]],
        umsatzsteuer: float = 0.0,
        vorsteuer: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Generate preview without creating XML file.

        Args:
            period: Fiscal period (YYYY-MM)
            invoices: List of invoices
            umsatzsteuer: Total output VAT
            vorsteuer: Total input VAT

        Returns:
            Preview data with Kennzahlen
        """
        kennzahlen = self._calculate_kennzahlen(invoices, umsatzsteuer, vorsteuer)

        year, month = period.split("-")

        # Calculate deadline (10th of following month)
        next_month = int(month) + 1
        next_year = int(year)
        if next_month > 12:
            next_month = 1
            next_year += 1

        deadline = f"{next_year}-{next_month:02d}-10"

        # Calculate days remaining
        today = datetime.now()
        deadline_dt = datetime(next_year, next_month, 10)
        days_remaining = (deadline_dt - today).days

        return {
            "period": period,
            "status": "preview",
            "kennzahlen": kennzahlen,
            "kz_81": kennzahlen.get("kz_81", 0.0),
            "kz_86": kennzahlen.get("kz_86", 0.0),
            "kz_83": kennzahlen.get("kz_83", 0.0),
            "kz_66": kennzahlen.get("kz_66", 0.0),
            "umsatzsteuer": kennzahlen.get("umsatzsteuer_total", 0.0),
            "vorsteuer": kennzahlen.get("vorsteuer_total", 0.0),
            "zahllast": kennzahlen.get("zahllast", 0.0),
            "invoices_included": len(invoices),
            "deadline": deadline,
            "days_remaining": days_remaining,
            "warnings": [],
        }
