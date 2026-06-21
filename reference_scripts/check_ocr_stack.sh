#!/usr/bin/env bash

set -euo pipefail

echo "Checking OCR / AI local stack"
echo

if command -v tesseract >/dev/null 2>&1; then
  echo "[OK] tesseract found"
  tesseract --version | head -n 1
else
  echo "[FAIL] tesseract not found"
  echo "Install with: sudo apt-get install -y tesseract-ocr tesseract-ocr-ell"
fi

echo
echo "Available Tesseract languages:"
if command -v tesseract >/dev/null 2>&1; then
  tesseract --list-langs || true
fi

echo
if command -v tesseract >/dev/null 2>&1; then
  if tesseract --list-langs 2>/dev/null | grep -qx "ell"; then
    echo "[OK] Greek OCR language 'ell' found"
  else
    echo "[FAIL] Greek OCR language 'ell' not found"
    echo "Install with: sudo apt-get install -y tesseract-ocr-ell"
  fi
fi

echo
if command -v ollama >/dev/null 2>&1; then
  echo "[OK] ollama found"
  ollama list || true
else
  echo "[WARN] ollama not found"
  echo "Install from: https://ollama.com/download/linux"
fi

echo
echo "Python package check:"
python3 - <<'PY'
packages = ["fitz", "pytesseract", "PIL", "cv2"]
for name in packages:
    try:
        __import__(name)
        print(f"[OK] {name}")
    except Exception as exc:
        print(f"[MISSING] {name}: {exc}")
PY
