"""
WINDI Ablehnungsbescheid Generator v1.0.0
Notificacao de Indeferimento - Bauantrag
27 Janeiro 2026
"""
from bescheid_generator import generate_bescheid_pdf

BEISPIEL_ABLEHNUNG = {
    'authority_name': 'Stadt Kempten (Allgaeu)',
    'department': 'Bauamt',
    'authority_address': 'Rathausplatz 1, 87435 Kempten',
    'authority_phone': '+49 831 2525-0',
    'authority_email': 'bauamt@kempten.de',
    'case_number': 'BG-2026-ABL-0001',
    'date': '',
    'recipient_name': '',
    'recipient_street': '',
    'recipient_city': '',
    'subject': 'Ablehnung Ihres Bauantrags',
    'subject_detail': '',
    'decision_type': 'ABGELEHNT',
    'conditions': [],
    'facts': [],
    'reasoning': [],
    'legal_basis': ['Art. 68 Abs. 1 BayBO', 'Art. 28 BayVwVfG'],
    'signatory_name': '',
    'signatory_title': 'Sachbearbeiter/in Bauamt',
    'author': 'Bauamt Kempten'
}

def generate_ablehnungsbescheid_pdf(data):
    merged = BEISPIEL_ABLEHNUNG.copy()
    merged.update(data)
    merged['decision_type'] = 'ABGELEHNT'
    return generate_bescheid_pdf(merged)

if __name__ == "__main__":
    pdf, receipt = generate_ablehnungsbescheid_pdf({'recipient_name': 'Test'})
    print(f"OK - {receipt['id']}")
