#!/bin/bash
# Move the site to its own domain once the domain is bought and its DNS points at GitHub Pages.
#
#   _ops/connect_domain.sh seawindowtides.com
#
# Before running: in Cloudflare DNS (DNS only, grey cloud) add
#   A     @    185.199.108.153 / 185.199.109.153 / 185.199.110.153 / 185.199.111.153
#   AAAA  @    2606:50c0:8000::153 / 2606:50c0:8001::153 / 2606:50c0:8002::153 / 2606:50c0:8003::153
#   CNAME www  atabany.github.io
# GitHub then serves the site at the root of the domain and 301-redirects every
# atabany.github.io/seawindow-site/... URL to the same path on the domain.
set -euo pipefail
domain=${1:?usage: connect_domain.sh <domain>}
cd "$(dirname "$0")/.."

dig +short @1.1.1.1 "$domain" A | sort | tr '\n' ' '; echo
python3 - "$domain" <<'EOF'
import json, sys
p = '_src/site.json'
c = json.load(open(p))
c['base'] = f'https://{sys.argv[1]}/'
open(p, 'w').write(json.dumps(c, indent=2, ensure_ascii=False) + '\n')
EOF
echo "$domain" > CNAME
python3 -I _ops/build.py
python3 -I _ops/validate.py
git add -A
git commit -m "Serve the site at https://$domain/"
git grep -nE '^(<<<<<<<|>>>>>>>)( |$)' && { echo 'conflict markers'; exit 1; } || true
git push git@github.com:Atabany/seawindow-site.git HEAD:main
gh api -X PUT repos/Atabany/seawindow-site/pages -f cname="$domain" >/dev/null
echo "Custom domain set. When GitHub has issued the certificate run:"
echo "  gh api -X PUT repos/Atabany/seawindow-site/pages -F https_enforced=true"
echo "  curl -sI https://$domain/ | head -3; curl -sI https://atabany.github.io/seawindow-site/support.html | grep -i location"
