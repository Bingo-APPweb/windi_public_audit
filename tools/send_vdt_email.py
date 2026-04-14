#!/usr/bin/env python3
"""
VDT Email Sender - IDT Kempten Outreach
WINDI Publishing House · I9 Gate Required
"""

import smtplib
import ssl
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime

# SMTP Configuration (Strato)
SMTP_HOST = "smtp.strato.de"
SMTP_PORT = 465

def send_vdt_email(
    smtp_user: str,
    smtp_pass: str,
    from_email: str,
    to_emails: list,
    cc_emails: list = None,
    pdf_path: str = None,
    test_mode: bool = True
):
    """
    Send VDT Concept Note email to IDT Kempten

    Args:
        smtp_user: SMTP username
        smtp_pass: SMTP password
        from_email: Sender email
        to_emails: List of recipient emails
        cc_emails: List of CC emails
        pdf_path: Path to PDF attachment
        test_mode: If True, adds [TEST] to subject
    """

    # Email content
    subject = "Forschungskooperation – Nachweisbarkeit digitaler Transformation / LeBi-Projekt"
    if test_mode:
        subject = f"[TEST] {subject}"

    body = """Sehr geehrte Frau Prof. Dr. Winkler,
sehr geehrte Frau Prof. Dr. Niedermeier,
sehr geehrte Frau Dr. Müller-Kreiner,

mein Name ist Jober Mögele Correa, ich bin in Kempten ansässig und arbeite an der Schnittstelle von digitaler Transformation, Governance und verifizierbaren Entscheidungssystemen.

Aus dieser Arbeit heraus hat sich ein Ansatz entwickelt, der eine strukturelle Lücke adressiert: Aktuelle Systeme können Transformationsprozesse dokumentieren – sie können jedoch nicht unabhängig nachweisen, ob diese tatsächlich wie definiert ausgeführt wurden.

Wir bezeichnen dies als den „Proof Gap".

Im Rahmen des PHO Framework (Proof of Human Oversight) untersuche ich, wie sich Entscheidungs- und Lernprozesse unabhängig auditierbar und kryptographisch verifizierbar machen lassen – insbesondere im Hinblick auf EU AI Act (Art. 14) und GDPR (Art. 22).

Ihre Arbeit am Institut für digitale Transformation in Arbeit, Bildung und Gesellschaft, insbesondere im Kontext des Interreg-Projekts LeBi, berührt genau den Bereich, in dem dieser Ansatz besonders relevant wird.

Mich interessiert insbesondere, wie sich dieser Ansatz im Kontext von organisationalem Lernen und Onboarding empirisch untersuchen lässt.

Eine mögliche gemeinsame Forschungsfrage wäre:

„Wie kann digitales Onboarding nicht nur strukturiert, sondern auch unabhängig nachweisbar gemacht werden?"

Im Anhang finden Sie ein kurzes Konzeptpapier, das den Ansatz skizziert.

Ich würde mich sehr über eine kurze, unverbindliche Rückmeldung per E-Mail freuen, um zu prüfen, ob hier eine inhaltliche Schnittmenge für eine gemeinsame Forschungsinitiative besteht.

Ich richte mich gerne nach Ihrem Zeitfenster.

Mit freundlichen Grüßen
Jober Mögele Correa
PHO Framework · WINDI Publishing House
Kempten, Bayern
"""

    # Create message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = ', '.join(to_emails)
    if cc_emails:
        msg['Cc'] = ', '.join(cc_emails)
    msg['Subject'] = subject

    # Attach body
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # Attach PDF if provided
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, 'rb') as f:
            pdf_attachment = MIMEApplication(f.read(), _subtype='pdf')
            pdf_attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=os.path.basename(pdf_path)
            )
            msg.attach(pdf_attachment)
        print(f"📎 PDF attached: {os.path.basename(pdf_path)}")

    # All recipients
    all_recipients = to_emails + (cc_emails or [])

    # Send email
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, all_recipients, msg.as_string())

        print(f"✅ Email sent successfully!")
        print(f"   From: {from_email}")
        print(f"   To: {', '.join(to_emails)}")
        if cc_emails:
            print(f"   Cc: {len(cc_emails)} recipients")
        print(f"   Subject: {subject}")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True

    except Exception as e:
        print(f"❌ Email failed: {str(e)}")
        return False


if __name__ == "__main__":
    import sys

    # Check arguments
    if len(sys.argv) < 3:
        print("Usage: python3 send_vdt_email.py <smtp_user> <smtp_pass> [--live]")
        print("")
        print("Test mode (default): sends to jober@a4desk.de only")
        print("Live mode (--live): sends to IDT Kempten with all CCs")
        sys.exit(1)

    smtp_user = sys.argv[1]
    smtp_pass = sys.argv[2]
    live_mode = "--live" in sys.argv

    # PDF path
    pdf_path = "/opt/windi/projects/vdt-kempten/VDT_Konzeptpapier_v1.1_DE.pdf"

    if live_mode:
        # LIVE MODE - Real recipients
        print("🔴 LIVE MODE - Sending to IDT Kempten")
        print("=" * 50)

        to_emails = [
            "katrin.winkler@hs-kempten.de",
            "sandra.niedermeier@hs-kempten.de",
            "claudia.mueller-kreiner@hs-kempten.de"
        ]
        cc_emails = [
            "jober@a4desk.de",
            "miriam.liebhart@hs-kempten.de",
            "esma.guendogan@hs-kempten.de",
            "lisa.herb@hs-kempten.de",
            "natascha.becker@hs-kempten.de",
            "franziska.dworschak@hs-kempten.de",
            "kai.niethammer@hs-kempten.de",
            "lothar.fuhr@hs-kempten.de",
            "manuela.eittingerchristians@hs-kempten.de"
        ]
        test_mode = False
    else:
        # TEST MODE - Send to self
        print("🟡 TEST MODE - Sending to jober@a4desk.de only")
        print("=" * 50)

        to_emails = ["jober@a4desk.de"]
        cc_emails = None
        test_mode = True

    # I9 Gate - Human confirmation
    print(f"\nRecipients: {to_emails}")
    if cc_emails:
        print(f"CC: {len(cc_emails)} assistants")
    print(f"PDF: {pdf_path}")
    print("")

    # Send
    success = send_vdt_email(
        smtp_user=smtp_user,
        smtp_pass=smtp_pass,
        from_email="jober@a4desk.de",
        to_emails=to_emails,
        cc_emails=cc_emails,
        pdf_path=pdf_path,
        test_mode=test_mode
    )

    sys.exit(0 if success else 1)
