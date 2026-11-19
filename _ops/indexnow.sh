#!/bin/sh
# Tell IndexNow (Bing, Yandex, Seznam, Naver) which URLs changed. Run after a push that adds or edits pages.
#   sh _ops/indexnow.sh                                   every URL in sitemap.xml
#   sh _ops/indexnow.sh https://seawindowtides.com/x.html  just these
# The key file 3f8cececeb7d7258969a0655486126c2.txt in the site root proves ownership; keep it published.
KEY=3f8cececeb7d7258969a0655486126c2
HOST=seawindowtides.com
cd "$(dirname "$0")/.."
if [ $# -gt 0 ]; then LIST=$(printf '"%s",' "$@" | sed 's/,$//')
else LIST=$(grep -o '<loc>[^<]*</loc>' sitemap.xml | sed 's/<[^>]*>//g; s/.*/"&"/' | paste -sd, -); fi
curl -s -o /dev/null -w "IndexNow HTTP %{http_code}\n" -X POST https://api.indexnow.org/indexnow \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "{\"host\":\"$HOST\",\"key\":\"$KEY\",\"keyLocation\":\"https://$HOST/$KEY.txt\",\"urlList\":[$LIST]}"
