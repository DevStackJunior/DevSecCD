#!/usr/bin/env python3
"""
Script pour envoyer les résultats d'analyse de sécurité vers le VPS
À exécuter depuis GitHub Actions
"""

import requests
import json
import os
import sys
import hmac
import hashlib
from datetime import datetime

# Configuration
VPS_URL = os.environ.get('VPS_URL', 'http://votre-vps-ip:5000')
VPS_SECRET = os.environ.get('VPS_SECRET_KEY', '')
RESULTS_FILE = os.environ.get('RESULTS_FILE', 'security_report.json')

def generate_signature(payload):
    """Génère une signature HMAC pour sécuriser la requête"""
    if not VPS_SECRET:
        return ''
    
    return hmac.new(
        VPS_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

def load_results():
    """Charge les résultats depuis le fichier JSON"""
    try:
        with open(RESULTS_FILE, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {RESULTS_FILE}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de parsing JSON: {e}")
        sys.exit(1)

def enrich_data(results):
    """Ajoute des métadonnées contextuelles aux résultats"""
    enriched = {
        'timestamp': datetime.now().isoformat(),
        'repository': os.environ.get('GITHUB_REPOSITORY', 'unknown'),
        'workflow': os.environ.get('GITHUB_WORKFLOW', 'unknown'),
        'run_id': os.environ.get('GITHUB_RUN_ID', 'unknown'),
        'run_number': os.environ.get('GITHUB_RUN_NUMBER', 'unknown'),
        'ref': os.environ.get('GITHUB_REF', 'unknown'),
        'sha': os.environ.get('GITHUB_SHA', 'unknown'),
        'actor': os.environ.get('GITHUB_ACTOR', 'unknown'),
        'results': results
    }
    return enriched

def send_to_vps(data):
    """Envoie les données vers le VPS"""
    try:
        endpoint = f"{VPS_URL}/api/results"
        payload = json.dumps(data)
        
        # Générer la signature
        signature = generate_signature(payload)
        
        headers = {
            'Content-Type': 'application/json',
            'X-Signature': signature
        }
        
        print(f"📤 Envoi des résultats vers {endpoint}...")
        
        response = requests.post(
            endpoint,
            data=payload,
            headers=headers,
            timeout=30
        )
        
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Envoi réussi!")
        print(f"   Réponse: {json.dumps(result, indent=2)}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur d'envoi: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Détails: {e.response.text}")
        return False

def main():
    """Fonction principale"""
    print("=" * 50)
    print("📊 Publication des résultats vers le VPS")
    print("=" * 50)
    
    # Charger les résultats
    print("\n1️⃣ Chargement des résultats...")
    results = load_results()
    print(f"   ✓ {len(results)} résultats chargés")
    
    # Enrichir avec les métadonnées
    print("\n2️⃣ Enrichissement des données...")
    enriched_data = enrich_data(results)
    print(f"   ✓ Repository: {enriched_data['repository']}")
    print(f"   ✓ Run ID: {enriched_data['run_id']}")
    
    # Envoyer vers le VPS
    print("\n3️⃣ Envoi vers le VPS...")
    success = send_to_vps(enriched_data)
    
    if success:
        print("\n✅ Publication terminée avec succès!")
        sys.exit(0)
    else:
        print("\n❌ Échec de la publication")
        sys.exit(1)

if __name__ == '__main__':
    main()