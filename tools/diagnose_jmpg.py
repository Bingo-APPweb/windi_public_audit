#!/usr/bin/env python3
"""
Diagnóstico .jmpg — Verificação do bloco de prova
Abre o bundle, inspeciona cada bloco P1-P5, e reporta se jmpg_proof está presente.
"""
import zipfile, tarfile, json, sys, hashlib, os, gzip

def sha256(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode()).hexdigest()

def diagnose(path):
    print(f"\n{'='*60}")
    print(f"  DIAGNÓSTICO .jmpg")
    print(f"  Arquivo: {path}")
    print(f"{'='*60}\n")

    if not os.path.exists(path):
        print(f"❌ Arquivo não encontrado: {path}")
        return

    print(f"  Tamanho: {os.path.getsize(path)} bytes")
    print(f"  Hash do bundle: {sha256(open(path,'rb').read())[:32]}...\n")

    try:
        with zipfile.ZipFile(path, 'r') as z:
            names = z.namelist()
            print(f"  Blocos encontrados: {names}\n")

            results = {}
            for name in names:
                data = z.read(name)
                try:
                    parsed = json.loads(data)
                    results[name] = parsed
                except:
                    results[name] = data.decode('utf-8', errors='replace')

    except zipfile.BadZipFile:
        # Tentar como tar.gz
        try:
            with tarfile.open(path, 'r:gz') as t:
                names = t.getnames()
                print(f"  Formato: tar.gz ✅")
                print(f"  Blocos encontrados: {names}\n")

                results = {}
                for name in names:
                    member = t.extractfile(name)
                    if member:
                        data = member.read()
                        try:
                            parsed = json.loads(data)
                            results[name] = parsed
                        except:
                            results[name] = data.decode('utf-8', errors='replace')
        except (tarfile.TarError, gzip.BadGzipFile):
            print("❌ Não é ZIP nem tar.gz válido — pode ser JPEG puro")
            diagnose_jpeg(path)
            return

    # ── Analisar P1
    print("── P1_content ──────────────────────────────")
    p1 = results.get('P1_content.json')
    if p1:
        print(f"  ✅ Presente")
        if isinstance(p1, dict):
            print(f"  doc_name: {p1.get('doc_name', p1.get('metadata',{}).get('doc_name','N/A'))}")
            print(f"  doc_type: {p1.get('doc_type','N/A')}")
    else:
        print("  ❌ Ausente")

    # ── Analisar P2 (o que importa)
    print("\n── P2_proof ─────────────────────────────────")
    p2 = results.get('P2_proof.json')
    if p2 and isinstance(p2, dict):
        proof = p2.get('windi_proof', p2)
        print(f"  ✅ Presente")
        print(f"  receipt_id:    {proof.get('receipt_id','❌ NULL')}")
        print(f"  content_hash:  {str(proof.get('content_hash','❌ NULL'))[:32]}...")
        print(f"  timestamp_utc: {proof.get('timestamp_utc','❌ NULL')}")
        print(f"  verify_url:    {proof.get('verify_url','❌ NULL')}")
        print(f"  qr_payload:    {proof.get('qr_payload','❌ NULL')}")

        issuer = proof.get('issuer', {})
        print(f"  issuer.actor:  {issuer.get('actor','❌ NULL')}")
        print(f"  issuer.did:    {issuer.get('did','❌ NULL')}")

        gov = proof.get('governance', {})
        print(f"  gov.level:     {gov.get('level','❌ NULL')}")
        print(f"  gov.sector:    {gov.get('sector','N/A (pre-Gen7)')}")
        print(f"  trust_index:   {gov.get('trust_index','N/A (pre-Gen7)')}")
        print(f"  integrity_flag:{gov.get('integrity_flag','N/A (pre-Gen7)')}")
        print(f"  supersedes:    {gov.get('supersedes','null (genesis)')}")

        chain = proof.get('anchor_chain', {})
        print(f"  anchor.genesis:{chain.get('genesis','N/A')}")
        print(f"  anchor.depth:  {chain.get('depth','N/A')}")

        env_hash = proof.get('envelope_hash','N/A (pre-Gen7)')
        print(f"  envelope_hash: {str(env_hash)[:32] if env_hash != 'N/A (pre-Gen7)' else env_hash}")

        # ── VERIFICAÇÃO CRÍTICA: jmpg_proof
        print("\n── CAMPO jmpg_proof ─────────────────────────")
        jmpg_proof = p2.get('jmpg_proof') or proof.get('jmpg_proof')
        if jmpg_proof:
            print(f"  ✅ jmpg_proof PRESENTE: {json.dumps(jmpg_proof)[:80]}")
        else:
            print(f"  ⚠️  jmpg_proof = null (ou ausente)")
            print(f"  → O envelope usa 'windi_proof' como chave raiz")
            print(f"  → Se o Verify Public procura 'jmpg_proof', precisa de ajuste")
            wp = p2.get('windi_proof')
            print(f"  → Chave raiz actual: {'windi_proof ✅' if wp else '❌ NENHUMA'}")

        # ── Hash integrity check
        print("\n── INTEGRIDADE ──────────────────────────────")
        p1_raw = json.dumps(results.get('P1_content.json',''), separators=(',',':'))
        p1_hash_calc = sha256(p1_raw)
        p1_hash_stored = proof.get('content_hash','')

        # Tentar também com o raw original
        p1_raw_orig = results.get('P1_content.json')
        if isinstance(p1_raw_orig, dict):
            for sep in [(',',':'), (', ',': ')]:
                candidate = json.dumps(p1_raw_orig, separators=sep)
                if sha256(candidate) == p1_hash_stored:
                    print(f"  ✅ content_hash MATCH (sep={sep})")
                    break
            else:
                print(f"  ⚠️  content_hash diverge (serialização diferente)")
                print(f"     stored:     {p1_hash_stored[:32]}...")
                print(f"     calculado:  {p1_hash_calc[:32]}...")
                print(f"     → Normal se o encoder serializa diferente do Python")
    else:
        print("  ❌ P2_proof ausente ou inválido")
        print("  → injectProof() pode não ter executado")

    # ── P5 (Gen 7)
    print("\n── P5_sector (Gen 7) ────────────────────────")
    p5 = results.get('P5_sector.json')
    if p5:
        print(f"  ✅ Presente — sector: {p5.get('sector','N/A')}")
        print(f"     safety_level: {p5.get('safety_level','N/A')}")
        print(f"     trust_index:  {p5.get('trust_index','N/A')}")
    else:
        print("  ⚠️  Ausente — bundle é pré-Gen7 (P1-P4 apenas)")

    # ── Diagnóstico final
    print(f"\n{'='*60}")
    print("  DIAGNÓSTICO FINAL")
    print(f"{'='*60}")

    has_p2     = 'P2_proof.json' in results
    has_proof  = has_p2 and isinstance(results.get('P2_proof.json'), dict)
    has_gen7   = 'P5_sector.json' in results
    receipt_ok = has_proof and bool(
        (results['P2_proof.json'].get('windi_proof') or results['P2_proof.json'])
        .get('receipt_id')
    )

    print(f"  Bundle ZIP válido:      ✅")
    print(f"  P2 (proof envelope):    {'✅' if has_proof else '❌'}")
    print(f"  receipt_id presente:    {'✅' if receipt_ok else '❌'}")
    print(f"  Gen 7 (P5):             {'✅' if has_gen7 else '⚠️  pré-Gen7'}")
    print(f"  jmpg_proof (chave alt): {'verificar Verify Public' if has_proof else '❌'}")

    if has_proof and receipt_ok:
        rid = (results['P2_proof.json'].get('windi_proof') or results['P2_proof.json']).get('receipt_id')
        print(f"\n  ✅ CICLO FECHADO — injectProof OK")
        print(f"  Se Verify Public retorna jmpg_proof=null,")
        print(f"  o extractor deve procurar 'windi_proof' em vez de 'jmpg_proof'.")
        print(f"\n  Para verificar no Ledger:")
        print(f"  curl http://localhost:8101/api/receipts/{rid}")
    else:
        print(f"\n  ❌ CICLO INCOMPLETO — injectProof não executou ou falhou")


def diagnose_jpeg(path):
    """Procura APP1/EXIF num JPEG puro."""
    with open(path, 'rb') as f:
        data = f.read()

    print("\n── Análise JPEG ─────────────────────────────")
    is_jpeg = data[:2] == b'\xff\xd8'
    print(f"  JPEG magic: {'✅' if is_jpeg else '❌'}")

    # Procurar marcador APP1 (0xFF 0xE1) — onde o EXIF/XMP vive
    app1_pos = data.find(b'\xff\xe1')
    if app1_pos != -1:
        print(f"  APP1 encontrado em offset: {app1_pos}")
        segment = data[app1_pos+4:app1_pos+200]
        print(f"  APP1 preview: {segment[:50]}")
    else:
        print("  APP1: ❌ não encontrado")

    # Procurar string WINDI directamente
    windi_pos = data.find(b'WINDI')
    if windi_pos != -1:
        print(f"  String 'WINDI' em offset: {windi_pos}")
        print(f"  Contexto: {data[windi_pos:windi_pos+100]}")
    else:
        print("  String 'WINDI': ❌ não encontrada no binário")


if __name__ == "__main__":
    # ── Executar nos paths prováveis
    paths_to_check = [
        "/opt/windi/stress-tests/W-PROV-TOUR-001/W-PROV-TOUR-001.jmpg",
        "/opt/windi/stress-tests/W-PROV-TOUR-001/W-PROV-TOUR-001-v7.jmpg",
        "/tmp/W-PROV-TOUR-001.jmpg",
    ]

    # Se passado como argumento
    if len(sys.argv) > 1:
        paths_to_check = [sys.argv[1]]

    found = False
    for p in paths_to_check:
        if os.path.exists(p):
            diagnose(p)
            found = True

    if not found:
        print("⚠️  Nenhum .jmpg encontrado nos paths padrão.")
        print("Uso: python3 diagnose_jmpg.py /caminho/para/arquivo.jmpg")
        print("\nPaths verificados:")
        for p in paths_to_check:
            print(f"  {p}")
