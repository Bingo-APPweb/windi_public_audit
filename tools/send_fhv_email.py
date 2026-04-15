#!/usr/bin/env python3
"""
FHV Email Sender - Julia Reiner (LeBi)
WINDI Publishing House · I9 Gate Required
Via Referência: Prof. Dr. Sandra Niedermeier (HS Kempten)
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

def send_fhv_email(
    smtp_user: str,
    smtp_pass: str,
    from_email: str,
    to_emails: list,
    pdf_path: str = None,
    test_mode: bool = True
):
    """
    Send PHO/LeBi email to Dr. Julia Reiner (FH Vorarlberg)
    """

    # Email content
    subject = "Anfrage – Nachweisbarkeit im Kontext LeBi"
    if test_mode:
        subject = f"[TEST] {subject}"

    body = """Sehr geehrte Frau Dr. Reiner,

mein Name ist Jober Mögele Correa, ich bin in Kempten ansässig und arbeite an der Schnittstelle von digitaler Transformation, Governance und verifizierbaren Entscheidungssystemen.

Frau Prof. Dr. Niedermeier von der Hochschule Kempten hat mich im Kontext des LeBi-Projekts an Sie verwiesen.

Aus meiner Arbeit heraus hat sich ein Ansatz entwickelt, der eine strukturelle Lücke adressiert:
Aktuelle Systeme können Transformationsprozesse dokumentieren, jedoch nicht unabhängig nachweisen, ob diese tatsächlich wie definiert ausgeführt wurden.

Wir bezeichnen dies als den „Proof Gap".

Im Rahmen des PHO Framework untersuche ich, wie sich Entscheidungs- und Lernprozesse so gestalten lassen, dass sie unabhängig auditierbar und kryptographisch verifizierbar werden.

Vor dem Hintergrund Ihres Projekts – insbesondere im Bereich Onboarding in KMUs – erscheint mir dieser Ansatz als eine mögliche ergänzende Perspektive.

Mich würde interessieren, ob und wie sich dieser Ansatz im Rahmen des LeBi-Projekts praktisch oder empirisch einordnen ließe.

Ich würde mich sehr über eine kurze, unverbindliche Rückmeldung per E-Mail freuen, um zu prüfen, ob hier eine inhaltliche Schnittmenge für eine gemeinsame Forschungsinitiative besteht.

Ich richte mich gerne nach Ihrer Verfügbarkeit.

Mit freundlichen Grüßen
Jober Mögele Correa
Kempten, Bayern
PHO Framework (WINDI System)
"""

    # Create message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = ', '.join(to_emails)
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

    # Send email
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, to_emails, msg.as_string())

        print(f"✅ Email sent successfully!")
        print(f"   From: {from_email}")
        print(f"   To: {', '.join(to_emails)}")
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
        print("Usage: python3 send_fhv_email.py <smtp_user> <smtp_pass> [--live]")
        print("")
        print("Test mode (default): sends to jober@a4desk.de only")
        print("Live mode (--live): sends to Dr. Julia Reiner (FHV)")
        sys.exit(1)

    smtp_user = sys.argv[1]
    smtp_pass = sys.argv[2]
    live_mode = "--live" in sys.argv

    # PDF path
    pdf_path = "/opt/windi/projects/vdt-kempten/VDT_Konzeptpapier_v1.1_DE.pdf"

    if live_mode:
        # LIVE MODE - Real recipient
        print("🔴 LIVE MODE - Sending to Dr. Julia Reiner (FH Vorarlberg)")
        print("=" * 50)
        to_emails = ["julia.reiner@fhv.at"]
        test_mode = False
    else:
        # TEST MODE - Send to self
        print("🟡 TEST MODE - Sending to jober@a4desk.de only")
        print("=" * 50)
        to_emails = ["jober@a4desk.de"]
        test_mode = True

    # I9 Gate - Human confirmation
    print(f"\nRecipient: {to_emails[0]}")
    print(f"PDF: {pdf_path}")
    print(f"Referência: Prof. Dr. Sandra Niedermeier (HS Kempten)")
    print("")

    # Send
    success = send_fhv_email(
        smtp_user=smtp_user,
        smtp_pass=smtp_pass,
        from_email="jober@a4desk.de",
        to_emails=to_emails,
        pdf_path=pdf_path,
        test_mode=test_mode
    )

    sys.exit(0 if success else 1)
