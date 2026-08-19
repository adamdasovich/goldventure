#!/bin/sh
# Restrict ChromaDB to localhost plus explicitly allowed GPU droplets.
#
# Chroma runs as `chroma run --host 0.0.0.0 --port 8002` with no authentication
# of any kind, so until this existed anyone who found the port could read every
# embedded document, insert poisoned vectors, or delete a collection outright.
# Binding to localhost is not an option: the on-demand GPU worker writes chunks
# to Chroma across the public internet from a droplet whose IP changes on every
# run.
#
# The rules live in their own chain, matched only on the Chroma port, so a
# mistake here cannot lock anyone out of SSH. The chain is rebuilt from the
# allowlist file on every change, which keeps it idempotent — the orchestrator
# calls `allow` when it creates a droplet and `revoke` when it destroys one,
# and a duplicate call is harmless.
#
#   chroma_firewall.sh init            rebuild the chain and hook it into INPUT
#   chroma_firewall.sh allow   <ip>    permit a droplet, then rebuild
#   chroma_firewall.sh revoke  <ip>    drop a droplet, then rebuild
#   chroma_firewall.sh status          show the live chain and the allowlist

set -e

CHAIN=CHROMA
PORT=8002
ALLOWLIST=/etc/goldventure/chroma_allowlist

valid_ip() {
    echo "$1" | grep -Eq '^([0-9]{1,3}\.){3}[0-9]{1,3}$' || return 1
    for octet in $(echo "$1" | tr '.' ' '); do
        [ "$octet" -le 255 ] 2>/dev/null || return 1
    done
    return 0
}

rebuild() {
    mkdir -p "$(dirname "$ALLOWLIST")"
    touch "$ALLOWLIST"

    iptables -N "$CHAIN" 2>/dev/null || true
    iptables -F "$CHAIN"

    # Django, Celery and the reindex commands all reach Chroma over loopback.
    iptables -A "$CHAIN" -i lo -j ACCEPT
    iptables -A "$CHAIN" -s 127.0.0.1/8 -j ACCEPT

    while read -r ip; do
        case "$ip" in ''|\#*) continue ;; esac
        if valid_ip "$ip"; then
            iptables -A "$CHAIN" -s "$ip" -j ACCEPT
        else
            echo "skipping malformed allowlist entry: $ip" >&2
        fi
    done < "$ALLOWLIST"

    iptables -A "$CHAIN" -j DROP

    # Hook into INPUT exactly once, whatever state we started from.
    iptables -C INPUT -p tcp --dport "$PORT" -j "$CHAIN" 2>/dev/null \
        || iptables -I INPUT 1 -p tcp --dport "$PORT" -j "$CHAIN"
}

case "$1" in
    init)
        rebuild
        echo "chroma firewall active on port $PORT"
        ;;
    allow)
        valid_ip "$2" || { echo "not an IPv4 address: $2" >&2; exit 1; }
        mkdir -p "$(dirname "$ALLOWLIST")"
        touch "$ALLOWLIST"
        grep -qxF "$2" "$ALLOWLIST" || echo "$2" >> "$ALLOWLIST"
        rebuild
        echo "allowed $2"
        ;;
    revoke)
        valid_ip "$2" || { echo "not an IPv4 address: $2" >&2; exit 1; }
        if [ -f "$ALLOWLIST" ]; then
            grep -vxF "$2" "$ALLOWLIST" > "$ALLOWLIST.tmp" || true
            mv "$ALLOWLIST.tmp" "$ALLOWLIST"
        fi
        rebuild
        echo "revoked $2"
        ;;
    status)
        echo "--- allowlist ($ALLOWLIST) ---"
        cat "$ALLOWLIST" 2>/dev/null || echo "(empty)"
        echo "--- live chain ---"
        iptables -L "$CHAIN" -n -v 2>/dev/null || echo "(chain not installed)"
        ;;
    *)
        echo "usage: $0 {init|allow <ip>|revoke <ip>|status}" >&2
        exit 1
        ;;
esac
