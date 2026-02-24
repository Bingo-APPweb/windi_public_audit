#!/usr/bin/env python3
"""
WINDI Multimodal OCR Engine — Local Autonomous Module
Zero external API dependency. Tesseract-based.

NOTE: Requires Tesseract system package:
  sudo apt-get install tesseract-ocr tesseract-ocr-deu tesseract-ocr-por tesseract-ocr-eng
"""
import hashlib, json, os
from datetime import datetime

# Check dependencies
try:
    import pytesseract
    from PIL import Image
    HAS_DEPS = True
    try:
        pytesseract.get_tesseract_version()
        TESSERACT_OK = True
    except Exception:
        TESSERACT_OK = False
except ImportError:
    HAS_DEPS = False
    TESSERACT_OK = False


class WindiOCR:
    SUPPORTED_LANGS = {'de': 'deu', 'en': 'eng', 'pt': 'por', 'auto': 'deu+eng+por'}

    def __init__(self):
        self.version = "1.0.0"
        self.engine = "tesseract-local"
        self.requires_api_key = False

    def extract_text(self, image_path: str, lang: str = 'auto') -> dict:
        if not TESSERACT_OK:
            return {"error": "Tesseract not installed", "success": False,
                    "install": "sudo apt-get install tesseract-ocr tesseract-ocr-deu tesseract-ocr-por tesseract-ocr-eng"}
        if not os.path.exists(image_path):
            return {"error": f"File not found: {image_path}", "success": False}
        tess_lang = self.SUPPORTED_LANGS.get(lang, 'deu+eng+por')
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang=tess_lang)
            return {
                "success": True, "text": text.strip(),
                "char_count": len(text.strip()), "word_count": len(text.split()),
                "lang_tesseract": tess_lang,
                "content_hash": hashlib.sha256(text.encode('utf-8')).hexdigest(),
                "source_file": os.path.basename(image_path),
                "engine": self.engine, "requires_api_key": False,
                "timestamp": datetime.utcnow().isoformat() + 'Z'
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def extract_with_confidence(self, image_path: str, lang: str = 'auto') -> dict:
        if not TESSERACT_OK:
            return {"error": "Tesseract not installed", "success": False}
        tess_lang = self.SUPPORTED_LANGS.get(lang, 'deu+eng+por')
        try:
            img = Image.open(image_path)
            data = pytesseract.image_to_data(img, lang=tess_lang, output_type=pytesseract.Output.DICT)
            words, confs = [], []
            for i, w in enumerate(data['text']):
                if w.strip() and int(data['conf'][i]) > 0:
                    words.append(w)
                    confs.append(int(data['conf'][i]))
            return {
                "success": True, "text": ' '.join(words), "word_count": len(words),
                "avg_confidence": round(sum(confs)/len(confs), 1) if confs else 0,
                "engine": self.engine, "requires_api_key": False
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    def health(self) -> dict:
        if not HAS_DEPS:
            return {"status": "degraded", "error": "pytesseract/Pillow not installed",
                    "requires_api_key": False, "autonomous": True}
        if not TESSERACT_OK:
            return {"status": "pending", "service": "windi-multimodal-ocr",
                    "engine": "tesseract-local", "error": "Tesseract binary not installed",
                    "install": "sudo apt-get install tesseract-ocr tesseract-ocr-deu tesseract-ocr-por tesseract-ocr-eng",
                    "requires_api_key": False, "autonomous": True}
        try:
            return {
                "status": "ok", "service": "windi-multimodal-ocr",
                "engine": "tesseract-local",
                "version": str(pytesseract.get_tesseract_version()),
                "languages": pytesseract.get_languages(),
                "requires_api_key": False, "autonomous": True
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    ocr = WindiOCR()
    h = ocr.health()
    print(json.dumps(h, indent=2))
    if h["status"] == "ok":
        print("✅ WINDI Multimodal OCR — LOCAL AUTONOMOUS — Ready")
    else:
        print(f"⚠️  WINDI Multimodal OCR — {h['status'].upper()} — Tesseract needs install")
