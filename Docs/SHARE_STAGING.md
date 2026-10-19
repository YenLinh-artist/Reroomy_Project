# Shared staging site for Re:Room

The team should use one deployed staging website when they need shared products,
uploaded photos, and orders. Each local checkout of the code has its own local
database and does not synchronize data automatically.

## Staging services

- **GitHub:** source code only.
- **Render:** runs the Django website from the `reroom-team-staging` branch.
- **Neon (or another PostgreSQL provider):** one PostgreSQL database shared by
  the deployed website.
- **Cloudinary:** stores product and consultation images outside the web server.

The staging settings are isolated in `reroomy_core/settings_staging.py`. Local
development keeps using `reroomy_core/settings.py` and `db.sqlite3`.

## Create the shared services

1. Create a PostgreSQL project and copy its connection string. Keep it private.
2. Create a Cloudinary account and copy its `CLOUDINARY_URL`. Keep it private.
3. Push the reviewed code to the GitHub branch `reroom-team-staging`.
4. In Render, create a Blueprint from that repository and select the
   `reroom-team-staging` branch. Render reads `render.yaml`.
5. When Render requests `DATABASE_URL` and `CLOUDINARY_URL`, enter the values
   from steps 1 and 2 in Render's environment settings. Never put either value
   in GitHub or send it in a team chat.
6. Wait for the deploy to finish. Render provides the team's shared URL.
7. In the Render Shell, create the first site administrator:

   ```sh
   python manage.py createsuperuser --settings=reroomy_core.settings_staging
   ```

8. Sign in to the staging website and create staff accounts for the team.
   Everyone then uses the same staging URL to add products and make COD demo
   orders; those records are stored in the shared PostgreSQL database.

## Important data boundaries

- Do not point everyone's local `runserver` at the shared database. Use the
  deployed website; it keeps database credentials on the server.
- `db.sqlite3`, local `media/`, `.env`, Python bytecode, and virtual environments
  are local files and must not be pushed to GitHub.
- Free hosting plans have sleep, quota, and retention limits. Back up staging
  data before relying on it for a final presentation. Product images are stored
  in Cloudinary so they survive a web service restart.
- Staging checkout currently records COD orders only. It does not charge a card.
