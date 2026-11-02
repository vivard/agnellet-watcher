#!/usr/bin/env python3
"""Surveille les ateliers de Patrick Agnellet et notifie dès qu'une place se libère.

Utilise l'API publique WooCommerce du site (plus fiable que de parser le HTML).
Notifications : ntfy.sh (push sur téléphone) et/ou e-mail via SMTP (Gmail).
Aucune dépendance externe : uniquement la bibliothèque standard Python.

Variables d'environnement (toutes optionnelles, au moins un canal recommandé) :
  NTFY_TOPIC       nom du topic ntfy.sh (ex: agnellet-a8f3k2-gautier)
  SMTP_USER        adresse Gmail qui envoie (ex: moi@gmail.com)
  SMTP_PASSWORD    mot de passe d'application Gmail (16 caractères)
  MAIL_TO          destinataire (par défaut : SMTP_USER)
  SMTP_HOST/PORT   par défaut smtp.gmail.com / 465
"""

import datetime
import html
import json
import os
import smtplib
import sys
import urllib.request
from email.message import EmailMessage
from pathlib import Path

API_URL = "https://patrick-agnellet.com/wp-json/wc/store/v1/products?category=atelier&per_page=100"
PAGE_URL = "https://patrick-agnellet.com/lecole-entre-nous/"
STATE_FILE = Path(__file__).with_name("state.json")


def fetch_ateliers():
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0 (atelier-watcher)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        products = json.load(resp)
    return {
        str(p["id"]): {
            "name": html.unescape(p["name"]),
            "url": p["permalink"],
            "in_stock": bool(p["is_in_stock"]),
        }
        for p in products
    }


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"ateliers": {}}


def save_state(ateliers):
    # Le champ "month" change une fois par mois : le commit qui en résulte évite que
    # GitHub désactive le workflow planifié après 60 jours sans activité.
    state = {"month": datetime.date.today().strftime("%Y-%m"), "ateliers": ateliers}
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n")


def notify_ntfy(title, body, click_url):
    topic = os.environ.get("NTFY_TOPIC")
    if not topic:
        return
    req = urllib.request.Request(
        f"https://ntfy.sh/{topic}",
        data=body.encode("utf-8"),
        headers={
            "Title": title.encode("utf-8"),
            "Priority": "urgent",
            "Tags": "cake",
            "Click": click_url,
        },
    )
    urllib.request.urlopen(req, timeout=30)
    print("Notification ntfy envoyée")
    return True


def notify_email(title, body):
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    if not (user and password):
        return
    msg = EmailMessage()
    msg["Subject"] = title
    msg["From"] = user
    msg["To"] = os.environ.get("MAIL_TO") or user
    msg.set_content(body)
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    with smtplib.SMTP_SSL(host, port, timeout=30) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    print("E-mail envoyé")
    return True


def main():
    previous = load_state()["ateliers"]
    current = fetch_ateliers()

    newly_available = [
        a for pid, a in current.items()
        if a["in_stock"] and not previous.get(pid, {}).get("in_stock", False)
    ]

    for a in current.values():
        print(f"{'DISPO  ' if a['in_stock'] else 'complet'}  {a['name']}")

    if newly_available:
        lines = [f"• {a['name']}\n  {a['url']}" for a in newly_available]
        title = f"Atelier Agnellet disponible ! ({len(newly_available)})"
        body = "Place(s) disponible(s) :\n\n" + "\n\n".join(lines) + f"\n\nTous les ateliers : {PAGE_URL}"
        click = newly_available[0]["url"] if len(newly_available) == 1 else PAGE_URL
        sent, failed = 0, 0
        for send in (lambda: notify_ntfy(title, body, click), lambda: notify_email(title, body)):
            try:
                sent += bool(send())
            except Exception as e:  # un canal en panne ne doit pas bloquer l'autre
                failed += 1
                print(f"Erreur de notification : {e}", file=sys.stderr)
        if failed and not sent:
            # Aucun canal n'a marché : on ne sauvegarde pas, pour réessayer au prochain passage.
            sys.exit(1)

    save_state(current)


if __name__ == "__main__":
    main()
