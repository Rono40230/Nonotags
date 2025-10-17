#!/bin/bash
# Script de CI basique pour Nonotags
# Lance les tests unitaires avant commit

set -e

echo "🚀 Lancement des tests unitaires Nonotags..."

# Vérifier que pytest est installé
if ! command -v pytest >/dev/null 2>&1; then
    echo "❌ pytest n'est pas installé. Installez-le avec: pip install pytest"
    exit 1
fi

# Aller dans le répertoire du projet
cd "$(dirname "$0")"

# Lancer les tests
echo "🧪 Exécution des tests..."
pytest tests/ -v --tb=short

# Vérifier la couverture si pytest-cov est disponible
if python3 -c "import pytest_cov" 2>/dev/null; then
    echo "📊 Calcul de la couverture..."
    pytest tests/ --cov=core --cov=services --cov=support --cov-report=term-missing
else
    echo "⚠️ pytest-cov non installé - calcul de couverture ignoré"
fi

echo "✅ Tous les tests sont passés !"