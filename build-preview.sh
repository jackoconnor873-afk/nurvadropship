#!/usr/bin/env bash
# Builds preview/index.html — a single self-contained HTML file with the theme's
# CSS and JS inlined. Open it in a browser, or paste it into a Shopify
# "Custom Liquid" section / page to use the design without uploading the theme.
#
# Usage:  ./build-preview.sh

set -euo pipefail
cd "$(dirname "$0")"

OUT="preview/index.html"

{
  cat <<'HEAD'
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#05070a">
<title>Nurva Performance — Breathe Better. Perform Better. Live Better.</title>
<meta name="description" content="Nurva premium performance nasal strips. Sweat-proof, drug-free, up to 10 hours of hold. Open your airway for training, recovery and deeper sleep.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Inter:wght@400;500;600;700&family=Montserrat:wght@600;700;800&display=swap">
<style>
HEAD

  cat assets/nurva.css

  cat <<'MID'
</style>
</head>
<body>
MID

  cat preview/_body.html

  cat <<'TAILOPEN'
<script>
TAILOPEN

  cat assets/nurva.js

  cat <<'TAIL'
</script>
</body>
</html>
TAIL
} > "$OUT"

echo "Built $OUT ($(wc -c < "$OUT") bytes)"
