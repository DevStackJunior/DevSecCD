# 🛡️ Pipeline de Gouvernance & Sécurité Automatisée (DevSecOps)

Ce projet implémente une infrastructure de **surveillance continue** pour sécuriser le cycle de vie d'une application. Il transforme la sécurité, autrefois étape finale et manuelle, en un processus invisible, systématique et automatisé.

## 📋 Vision Stratégique
Dans un environnement de développement moderne, ce pipeline garantit que la rapidité ne compromet jamais l'intégrité des données. Il agit comme un **audit permanent**, assurant que chaque modification de code répond aux exigences de cybersécurité avant même d'être déployée.
<img width="889" height="499" alt="image" src="https://github.com/user-attachments/assets/c38c86ac-fbc4-458c-a058-5a461cf0de8a" />

---

## 🚀 Valeur Ajoutée pour l'Entreprise

* **Réduction des Risques :** Détection précoce des failles (mots de passe en clair, vulnérabilités critiques) avant qu'elles n'atteignent la production.
* **Conformité Internationale :** Alignement avec les standards **OWASP**, facilitant les certifications de type ISO ou les audits de conformité clients.
* **Optimisation des Coûts :** Corriger une faille durant la phase de conception coûte statistiquement beaucoup moins cher que de traiter un incident après une cyberattaque.
* **Traçabilité Totale :** Archivage automatique de chaque scan, créant un historique de santé du projet inaltérable et facile à consulter.

---

## ⚙️ Fonctionnement Technique (Sous le capot)

Le projet utilise le concept de **GitHub Actions**, des "robots" qui exécutent des tâches précises selon des règles prédéfinies :



1.  **Déclenchement (Trigger) :** Le système s'active automatiquement lors d'un ajout de code ou via une tâche planifiée chaque nuit à **02h00 UTC**.
2.  **Préparation :** Un environnement virtuel sécurisé et isolé est créé (Ubuntu + Python 3.11).
3.  **Exécution des Scripts de Sécurité :**
    * `run_security_scan.sh` : Analyse le code source pour trouver des faiblesses.
    * `run_owasp_ingest.sh` : Récupère et centralise les données de sécurité basées sur les standards OWASP.
4.  **Auto-Actualisation :** Si le scan produit de nouveaux résultats, le robot effectue lui-même un "Commit" (une sauvegarde) pour mettre à jour les dossiers de rapports (`statements/` et `analysis/`) sans intervention humaine.

---

## ⚠️ Limites et Points de Vigilance

Bien que performant, ce système automatisé présente des limites structurelles qu'il est important de piloter :

* **Faux Positifs :** Les outils automatiques peuvent parfois signaler des alertes qui ne sont pas de réelles menaces dans leur contexte spécifique. Une expertise humaine reste nécessaire pour valider les rapports les plus critiques.
* **Périmètre de Détection :** Le pipeline détecte les erreurs de configuration et les failles connues. Il ne remplace pas un "Pentest" (test d'intrusion) réalisé par un humain pour tester la logique métier complexe.
* **Dépendance à l'Infrastructure :** Le bon fonctionnement dépend de la disponibilité des services GitHub et des bases de données de vulnérabilités externes.
* **Course contre la montre :** Le système est efficace contre les menaces répertoriées. Les attaques de type "Zero-Day" (nouvelles failles non encore documentées) demandent une vigilance complémentaire.

---

## 🛠️ Stack Technique
* **Orchestration :** GitHub Actions
* **Langage :** Python 3.11
* **Rapports :** JSON (pour l'analyse de données) et Artifacts (pour le stockage).

---
*Document généré pour la documentation technique et la conformité projet.*
