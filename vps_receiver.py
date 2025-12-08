#!/usr/bin/env python3
"""
API Flask pour recevoir les résultats depuis GitHub Actions
À exécuter sur le VPS
"""

from flask import Flask, request, jsonify
import json
import os
from datetime import datetime
import hmac
import hashlib

app = Flask(__name__)

# Clé secrète pour authentifier les requêtes (à changer!)
SECRET_KEY = os.environ.get('VPS_SECRET_KEY', 'votre_cle_secrete_ici')

# Dossier de stockage des résultats
RESULTS_DIR = '/var/vps-results'
os.makedirs(RESULTS_DIR, exist_ok=True)

def verify_signature(payload, signature):
    """Vérifie la signature HMAC pour sécuriser les requêtes"""
    expected_signature = hmac.new(
        SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint de santé pour vérifier que le service fonctionne"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/results', methods=['POST'])
def receive_results():
    """
    Endpoint pour recevoir les résultats de sécurité depuis GitHub Actions
    """
    try:
        # Récupérer la signature pour vérification
        signature = request.headers.get('X-Signature', '')
        payload = request.get_data(as_text=True)
        
        # Vérifier la signature (optionnel mais recommandé)
        if signature and not verify_signature(payload, signature):
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Récupérer les données JSON
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Générer un nom de fichier unique
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        repo_name = data.get('repository', 'unknown').replace('/', '_')
        filename = f"{repo_name}_{timestamp}.json"
        filepath = os.path.join(RESULTS_DIR, filename)
        
        # Sauvegarder les résultats
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Résultats reçus et sauvegardés: {filename}")
        
        return jsonify({
            'status': 'success',
            'message': 'Results received and stored',
            'filename': filename,
            'timestamp': timestamp
        }), 200
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/results', methods=['GET'])
def list_results():
    """Liste tous les résultats stockés"""
    try:
        files = os.listdir(RESULTS_DIR)
        results = []
        
        for file in sorted(files, reverse=True):
            filepath = os.path.join(RESULTS_DIR, file)
            stat = os.stat(filepath)
            results.append({
                'filename': file,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return jsonify({
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/results/<filename>', methods=['GET'])
def get_result(filename):
    """Récupère un résultat spécifique"""
    try:
        filepath = os.path.join(RESULTS_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # En développement
    app.run(host='0.0.0.0', port=5000, debug=True)
    
    # En production, utiliser gunicorn:
    # gunicorn -w 4 -b 0.0.0.0:5000 vps_receiver:app