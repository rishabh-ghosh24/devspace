#!/bin/bash
# ---------------------------------------------------------------------------
# generate-traffic.sh — Hit all StayEasy routes to generate APM traces
#
# Includes successful requests, error cases (404, 409, 400), and the
# slow occupancy report to demonstrate latency detection in APM.
#
# Usage:  bash generate-traffic.sh [BASE_URL]
#         bash generate-traffic.sh                    # defaults to localhost
#         bash generate-traffic.sh http://130.61.28.142
# ---------------------------------------------------------------------------

BASE="${1:-http://localhost}"
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m"

echo "============================================"
echo " StayEasy Traffic Generator"
echo " Target: $BASE"
echo "============================================"
echo ""

# --- Helper ---
hit() {
    local label="$1"; shift
    local expect="$1"; shift
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" "$@")
    if [ "$code" == "$expect" ]; then
        echo -e "  ${GREEN}✓${NC} [$code] $label"
    else
        echo -e "  ${RED}✗${NC} [$code] $label (expected $expect)"
    fi
}

# ──────────────────────────────────────────────
echo "── Healthy requests ──"
# ──────────────────────────────────────────────

hit "GET /" "200" "$BASE/"

hit "GET /hotels" "200" "$BASE/hotels"

hit "GET /hotels/1" "200" "$BASE/hotels/1"

hit "GET /hotels/2" "200" "$BASE/hotels/2"

hit "GET /hotels/1/rooms" "200" "$BASE/hotels/1/rooms"

hit "GET /rooms/search (London)" "200" \
    "$BASE/rooms/search?city=London&check_in=2025-07-01&check_out=2025-07-05&guests=2"

hit "GET /rooms/search (Brighton)" "200" \
    "$BASE/rooms/search?city=Brighton&check_in=2025-08-10&check_out=2025-08-15&guests=2"

hit "GET /rooms/search (Edinburgh)" "200" \
    "$BASE/rooms/search?city=Edinburgh&check_in=2025-09-01&check_out=2025-09-03&guests=1"

hit "GET /reservations/1" "200" "$BASE/reservations/1"

hit "GET /reservations/2" "200" "$BASE/reservations/2"

hit "GET /guests/1/reservations" "200" "$BASE/guests/1/reservations"

hit "GET /guests/3/reservations" "200" "$BASE/guests/3/reservations"

hit "GET /reports/revenue" "200" "$BASE/reports/revenue"

echo ""
echo "── Slow request (1.5s delay) ──"

hit "GET /reports/occupancy" "200" "$BASE/reports/occupancy"

echo ""
echo "── Booking (success) ──"

# Book a room — should succeed
BOOK_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/reservations" \
    -H "Content-Type: application/json" \
    -d '{"guest_id":2,"room_id":10,"check_in":"2025-11-01","check_out":"2025-11-04","payment_method":"debit_card"}')
BOOK_CODE=$(echo "$BOOK_RESP" | tail -1)
BOOK_BODY=$(echo "$BOOK_RESP" | head -1)
if [ "$BOOK_CODE" == "201" ]; then
    echo -e "  ${GREEN}✓${NC} [201] POST /reservations — booking created"
else
    echo -e "  ${YELLOW}~${NC} [$BOOK_CODE] POST /reservations — $BOOK_BODY"
fi

echo ""
echo "── Error cases (expected failures) ──"

# 404 — hotel not found
hit "GET /hotels/999 (not found)" "404" "$BASE/hotels/999"

# 404 — reservation not found
hit "GET /reservations/999 (not found)" "404" "$BASE/reservations/999"

# 404 — guest not found
hit "GET /guests/999/reservations (not found)" "404" "$BASE/guests/999/reservations"

# 400 — missing required fields
hit "POST /reservations (missing fields)" "400" \
    -X POST "$BASE/reservations" \
    -H "Content-Type: application/json" \
    -d '{"guest_id":1}'

# 400 — invalid date format
hit "POST /reservations (bad dates)" "400" \
    -X POST "$BASE/reservations" \
    -H "Content-Type: application/json" \
    -d '{"guest_id":1,"room_id":1,"check_in":"not-a-date","check_out":"2025-05-05","payment_method":"credit_card"}'

# 400 — check_out before check_in
hit "POST /reservations (checkout < checkin)" "400" \
    -X POST "$BASE/reservations" \
    -H "Content-Type: application/json" \
    -d '{"guest_id":1,"room_id":1,"check_in":"2025-06-10","check_out":"2025-06-05","payment_method":"credit_card"}'

# 404 — guest not found in reservation
hit "POST /reservations (bad guest)" "404" \
    -X POST "$BASE/reservations" \
    -H "Content-Type: application/json" \
    -d '{"guest_id":999,"room_id":1,"check_in":"2025-07-01","check_out":"2025-07-03","payment_method":"credit_card"}'

# 404 — room not found in reservation
hit "POST /reservations (bad room)" "404" \
    -X POST "$BASE/reservations" \
    -H "Content-Type: application/json" \
    -d '{"guest_id":1,"room_id":999,"check_in":"2025-07-01","check_out":"2025-07-03","payment_method":"credit_card"}'

# 409 — double booking (book same room as seed data)
hit "POST /reservations (double booking)" "409" \
    -X POST "$BASE/reservations" \
    -H "Content-Type: application/json" \
    -d '{"guest_id":2,"room_id":5,"check_in":"2025-03-21","check_out":"2025-03-22","payment_method":"credit_card"}'

# 400 — search missing params
hit "GET /rooms/search (missing city)" "400" \
    "$BASE/rooms/search?check_in=2025-07-01&check_out=2025-07-05"

echo ""
echo "── Burst traffic (generates many traces quickly) ──"

for i in $(seq 1 5); do
    hit "GET /hotels (burst $i)" "200" "$BASE/hotels" &
done
wait
echo "  (5 parallel hotel list requests)"

for i in $(seq 1 3); do
    hit "GET /rooms/search London (burst $i)" "200" \
        "$BASE/rooms/search?city=London&check_in=2025-12-0${i}&check_out=2025-12-0$((i+2))&guests=2" &
done
wait
echo "  (3 parallel room searches — 30+ DB spans total)"

echo ""
echo "── Full booking workflow (search → book → verify) ──"

echo "  Step 1: Search for rooms in Edinburgh..."
SEARCH=$(curl -s "$BASE/rooms/search?city=Edinburgh&check_in=2025-12-01&check_out=2025-12-05&guests=2")
echo -e "  ${GREEN}✓${NC} Search complete"

echo "  Step 2: Book Highland Lodge Cabin..."
BOOK2=$(curl -s -w "\n%{http_code}" -X POST "$BASE/reservations" \
    -H "Content-Type: application/json" \
    -d '{"guest_id":3,"room_id":10,"check_in":"2025-12-01","check_out":"2025-12-05","payment_method":"credit_card"}')
BOOK2_CODE=$(echo "$BOOK2" | tail -1)
echo -e "  ${GREEN}✓${NC} [$BOOK2_CODE] Booking submitted"

echo "  Step 3: Look up the reservation..."
hit "GET /reservations/7 (just booked)" "200" "$BASE/reservations/7"

echo "  Step 4: Check guest history..."
hit "GET /guests/3/reservations" "200" "$BASE/guests/3/reservations"

echo "  Step 5: Check occupancy impact (slow)..."
hit "GET /reports/occupancy" "200" "$BASE/reports/occupancy"

echo "  Step 6: Check revenue impact..."
hit "GET /reports/revenue" "200" "$BASE/reports/revenue"

echo ""
echo "============================================"
echo " Done! Check OCI APM Trace Explorer now."
echo " You should see ~40 traces with a mix of"
echo " 200, 201, 400, 404, and 409 status codes."
echo " Look for:"
echo "   • /rooms/search — 10+ DB spans per trace"
echo "   • /reservations POST — 6 DB spans (INSERT)"
echo "   • /reports/occupancy — 1.5s latency spike"
echo "   • Error traces with 400/404/409 codes"
echo "============================================"
