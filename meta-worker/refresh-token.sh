#!/bin/bash
# Mint a non-expiring Facebook Page token and load it into the Worker.
#
# Graph API Explorer only issues short-lived tokens (~1-2 hours). A Page token
# inherits the lifetime of the User token it came from, so the fix is to first
# exchange the short-lived User token for a long-lived one, THEN derive the Page
# token from that. Page tokens built this way do not expire.
#
# Run from the meta-worker directory:  ./refresh-token.sh

set -euo pipefail

API="https://graph.facebook.com/v18.0"

echo
echo "Values live at: developers.facebook.com -> My Apps -> HomePowerRebate"
echo "                Worker -> App settings -> Basic"
echo

read -r  -p "App ID:                    " APP_ID
read -rs -p "App secret (hidden):       " APP_SECRET; echo
echo
echo "Now generate a fresh User Token in Graph API Explorer with"
echo "pages_show_list, pages_manage_posts and pages_read_engagement ticked."
echo
read -r  -p "User token:                " USER_TOKEN
echo

jsonval() { python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('$1',''))"; }

echo "[1/4] Exchanging for a long-lived user token..."
LONG_RESP=$(curl -sS -G "$API/oauth/access_token" \
  --data-urlencode "grant_type=fb_exchange_token" \
  --data-urlencode "client_id=$APP_ID" \
  --data-urlencode "client_secret=$APP_SECRET" \
  --data-urlencode "fb_exchange_token=$USER_TOKEN")

LONG_TOKEN=$(printf '%s' "$LONG_RESP" | jsonval access_token)
if [ -z "$LONG_TOKEN" ]; then
  echo "      FAILED. Facebook said:"
  printf '      %s\n' "$LONG_RESP"
  echo
  echo "      'Session has expired' means the user token went stale — generate"
  echo "      a new one in the Explorer and run this again."
  exit 1
fi
echo "      ok"

echo "[2/4] Deriving the page token..."
PAGES=$(curl -sS "$API/me/accounts?access_token=$LONG_TOKEN")
PAGE_TOKEN=$(printf '%s' "$PAGES" | python3 -c "
import sys,json
d=json.load(sys.stdin).get('data',[])
print(d[0]['access_token'] if d else '')
")
PAGE_ID=$(printf '%s' "$PAGES" | python3 -c "
import sys,json
d=json.load(sys.stdin).get('data',[])
print(d[0]['id'] if d else '')
")

if [ -z "$PAGE_TOKEN" ]; then
  echo "      FAILED — no pages returned. Confirm pages_show_list was ticked."
  printf '      %s\n' "$PAGES"
  exit 1
fi
echo "      ok — page $PAGE_ID"

echo "[3/4] Confirming the token does not expire..."
DEBUG=$(curl -sS "$API/debug_token?input_token=$PAGE_TOKEN&access_token=$LONG_TOKEN")
printf '%s' "$DEBUG" | python3 -c "
import sys,json
d=json.load(sys.stdin).get('data',{})
exp=d.get('expires_at',0)
scopes=','.join(d.get('scopes',[]))
print('      expires_at:', 'never' if exp==0 else exp)
print('      scopes:    ', scopes)
if exp!=0:
    print('      WARNING: still short-lived. Re-check the app secret.')
"

echo "[4/4] Writing to the Worker secret..."
printf '%s' "$PAGE_TOKEN" | npx wrangler secret put META_ACCESS_TOKEN >/dev/null 2>&1
printf '%s' "$PAGE_ID"    | npx wrangler secret put FACEBOOK_PAGE_ID  >/dev/null 2>&1
echo "      ok"

echo
echo "Done. Verify with:"
echo "  curl -X POST https://meta-automation.samuelmenard.workers.dev/test"
echo
