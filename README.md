# Surveillance des ateliers Patrick Agnellet

Toutes les 5 minutes, GitHub Actions interroge le site (catégorie « atelier ») et envoie
une notification dès qu'un atelier passe de **COMPLET** à **disponible**
(nouvel atelier publié avec des places, ou place libérée après une annulation).

Gratuit : un dépôt GitHub **public** a des minutes Actions illimitées.

## Mise en place (10 min)

1. **Créer un dépôt public** sur GitHub (ex. `agnellet-watcher`) et y pousser ce dossier :
   ```bash
   git init && git add . && git commit -m "init" && git branch -M main
   git remote add origin https://github.com/<vous>/agnellet-watcher.git
   git push -u origin main
   ```

2. **Notification push sur téléphone (recommandé, instantané)**
   - Installer l'app **ntfy** (iOS / Android, gratuite, sans compte).
   - S'abonner à un topic au nom difficile à deviner, ex. `agnellet-k7p2x9q`.

3. **E-mail (optionnel)** via Gmail :
   - Activer la validation en 2 étapes sur le compte Google, puis créer un
     *mot de passe d'application* : https://myaccount.google.com/apppasswords

4. Dans le dépôt : **Settings → Secrets and variables → Actions → New repository secret**

   | Secret          | Valeur                                    |
   |-----------------|-------------------------------------------|
   | `NTFY_TOPIC`    | `agnellet-k7p2x9q` (votre topic)          |
   | `SMTP_USER`     | `al.vivard@gmail.com`                     |
   | `SMTP_PASSWORD` | le mot de passe d'application (16 car.)   |
   | `MAIL_TO`       | `al.vivard@gmail.com`                     |

5. **Tester** : onglet **Actions → Surveillance ateliers Agnellet → Run workflow**.
   Le log affiche la liste des ateliers (complet / DISPO).

## Bon à savoir

- GitHub ne garantit pas la ponctualité du cron : en pratique un passage toutes les 5 à 15 min.
- `state.json` est commité automatiquement pour mémoriser l'état et ne pas
  renvoyer la même alerte à chaque passage (et une fois par mois pour éviter que GitHub
  désactive le workflow après 60 jours d'inactivité).
- Test local : `python3 check_ateliers.py`
