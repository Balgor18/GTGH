from flask import Flask, Response
from prometheus_client import Gauge, generate_latest
import threading
import requests
import os
import sqlite3
import sys
from datetime import datetime, timezone
from colorama import Fore, Style, init
import time

# Initialisation de la coloration du terminal (utile pour les logs locaux)
init(autoreset=True)

# Chargement du token d'environnement
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    print("❌ GITHUB_TOKEN non défini dans les variables d'environnement.")
    sys.exit(1)

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# Prometheus metrics
VIEWS_GAUGE = Gauge('github_repo_views', 'Nombre de vues uniques par repo', ['repo'])
CLONES_GAUGE = Gauge('github_repo_clones', 'Nombre de clones uniques par repo', ['repo'])

# Flask app pour exposer /metrics
app = Flask(__name__)

def get_my_repositories():
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/user/repos?visibility=public&affiliation=owner&per_page=100&page={page}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print("Erreur lors de la récupération des repos :", response.status_code)
            break
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def get_traffic_data(owner, repo, endpoint):
    url = f"https://api.github.com/repos/{owner}/{repo}/traffic/{endpoint}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erreur pour {repo} - {endpoint} : {response.status_code}")
        return None

def get_last_saved_stats(repo_name, cursor):
    cursor.execute("""
    SELECT views, clones FROM traffic
    WHERE repo_name = ?
    """, (repo_name,))
    return cursor.fetchone()

def save_stats(repo_name, views, clones, cursor, conn):
    cursor.execute("""
    INSERT OR REPLACE INTO traffic (repo_name, date, views, clones)
    VALUES (?, ?, ?, ?)
    """, (repo_name, datetime.now(timezone.utc).isoformat(), views, clones))
    conn.commit()

def collect_metrics():
    # Connexion SQLite dans ce thread
    conn = sqlite3.connect("traffic_data.db")
    cursor = conn.cursor()

    # S'assurer que la table existe
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS traffic (
        repo_name TEXT PRIMARY KEY,
        date TEXT,
        views INTEGER,
        clones INTEGER
    )
    """)
    conn.commit()

    while True:
        print("📊 Récupération des données GitHub...")
        repos = get_my_repositories()
        for repo in repos:
            name = repo['name']
            owner = repo['owner']['login']

            views_data = get_traffic_data(owner, name, "views")
            clones_data = get_traffic_data(owner, name, "clones")

            if not views_data or not clones_data:
                continue

            views = views_data["uniques"]
            clones = clones_data["uniques"]

            # Met à jour Prometheus
            VIEWS_GAUGE.labels(repo=name).set(views)
            CLONES_GAUGE.labels(repo=name).set(clones)

            # Sauvegarde SQLite
            save_stats(name, views, clones, cursor, conn)

        print("✅ Données mises à jour. Pause 1h.")
        time.sleep(3600)  # Pause de 1 heure entre chaque récupération

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

if __name__ == "__main__":
    threading.Thread(target=collect_metrics, daemon=True).start()
    app.run(host="0.0.0.0", port=8000)
