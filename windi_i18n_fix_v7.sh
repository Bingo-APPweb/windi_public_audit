#!/bin/bash
echo "=== WINDI i18n FIX v7.0 - Agent + Gateway lang support ==="

# Backup
AGENT="/opt/windi/engine/windi_agent_v3.py"
GATEWAY="/opt/windi/gateway/windi_gateway.py"
BACKUP_A="/opt/windi/backups/windi_agent_v3_pre_i18n_v7_$(date +%Y%m%d_%H%M).py"
BACKUP_G="/opt/windi/backups/windi_gateway_pre_i18n_v7_$(date +%Y%m%d_%H%M).py"

echo "Backups: $BACKUP_A, $BACKUP_G"
cp "$AGENT" "$BACKUP_A"
cp "$GATEWAY" "$BACKUP_G"

echo ""
echo "Step 1: Modifying ask_windi to accept lang..."
sed -i 's/def ask_windi(message: str) -> Dict:/def ask_windi(message: str, lang: str = "de") -> Dict:/g' "$AGENT"
sed -i 's/return get_windi_agent().process(message)/return get_windi_agent().process(message, lang=lang)/g' "$AGENT"

echo "Step 2: Modifying process to accept lang..."
sed -i 's/def process(self, user_message: str, context: Dict = None) -> Dict:/def process(self, user_message: str, context: Dict = None, lang: str = None) -> Dict:/g' "$AGENT"

echo "Step 3: Use passed lang instead of only detecting..."
sed -i 's/lang = self._detect_language(user_message)/lang = lang or self._detect_language(user_message)/g' "$AGENT"

echo "Step 4: Adding lang to ChatRequest..."
sed -i 's/dragon: str = "claude"/dragon: str = "claude"\n    lang: str = "de"/g' "$GATEWAY"

echo "Step 5: Passing lang to ask_windi..."
sed -i 's/result = ask_windi(full_message)/result = ask_windi(full_message, lang=req.lang)/g' "$GATEWAY"

echo "Step 6: Fix PT hardcoded strings in Gateway..."
sed -i 's/DOCUMENTO PARA ANÁLISE/DOCUMENT FOR ANALYSIS/g' "$GATEWAY"
sed -i 's/SOLICITAÇÃO DO USUÁRIO/USER REQUEST/g' "$GATEWAY"

echo ""
echo "Validating Agent..."
if python3 -m py_compile "$AGENT" 2>/dev/null; then
    echo "   Agent OK"
else
    echo "   Agent ERROR - rollback"
    cp "$BACKUP_A" "$AGENT"
    exit 1
fi

echo "Validating Gateway..."
if python3 -m py_compile "$GATEWAY" 2>/dev/null; then
    echo "   Gateway OK"
else
    echo "   Gateway ERROR - rollback"
    cp "$BACKUP_G" "$GATEWAY"
    exit 1
fi

echo ""
echo "Changes in Agent:"
diff "$BACKUP_A" "$AGENT" | head -20

echo ""
echo "Changes in Gateway:"
diff "$BACKUP_G" "$GATEWAY" | head -20

echo ""
echo "Done!"
echo "Rollback Agent: cp $BACKUP_A $AGENT"
echo "Rollback Gateway: cp $BACKUP_G $GATEWAY"
