# Deployment Walkthrough — Wild Kingdom Zoo Store

This guide walks you through deploying the zoo store on your Ludus Cyber Range machine
(Ubuntu/Debian) using the Ludus web console. No prior Docker or server experience needed.

---

## What is Docker?

Think of Docker as a packaging system. Instead of manually installing Node.js, a database,
and a web server — Docker bundles everything the app needs into self-contained "containers"
that just work. `docker-compose` lets you start all the containers at once with one command.

---

## Step 1 — Open Your Terminal

In the Ludus web console, open a terminal on your target Ubuntu machine.

You should see a prompt like:
```
user@machine:~$
```

Everything you type goes after the `$`.

---

## Step 2 — Update the System

Run these two commands. They make sure your machine has the latest software lists:

```bash
sudo apt update
sudo apt upgrade -y
```

> **What is `sudo`?** It means "run this as administrator." You may be asked for a password.

---

## Step 3 — Install Docker

Run this command. It downloads and runs Docker's official install script:

```bash
curl -fsSL https://get.docker.com | sudo sh
```

This takes 1–2 minutes. When it finishes, verify Docker is installed:

```bash
docker --version
```

You should see something like: `Docker version 26.x.x`

---

## Step 4 — Let Your User Run Docker

By default, only the root user can run Docker. This command adds your current user to the
Docker group so you don't need `sudo` every time:

```bash
sudo usermod -aG docker $USER
```

Then apply the change **without logging out** by running:

```bash
newgrp docker
```

Verify it worked:

```bash
docker run hello-world
```

You should see a "Hello from Docker!" message.

---

## Step 5 — Install Docker Compose

Docker Compose is the tool that reads the `docker-compose.yml` file and starts all the
containers together. It's included with modern Docker, but run this to be sure:

```bash
docker compose version
```

If you see a version number, you're good. If you get an error, install it:

```bash
sudo apt install -y docker-compose-plugin
```

---

## Step 6 — Install Git and Download the Code

Git is how you download the project code. Install it:

```bash
sudo apt install -y git
```

Now download (clone) the zoo store repository:

```bash
git clone <YOUR_REPO_URL> zoo-store
cd zoo-store
```

> Replace `<YOUR_REPO_URL>` with the actual URL of your repository.
> After running `cd zoo-store`, your prompt will show you're inside the project folder.

Verify the files are there:

```bash
ls
```

You should see: `backend/`, `frontend/`, `docker-compose.yml`, `README.md`, etc.

---

## Step 7 — Set a Secret Key

The app uses a secret key to secure user logins. You should change the default before
going live. Open the docker-compose file:

```bash
nano docker-compose.yml
```

Find this line:
```
- JWT_SECRET=change-me-in-production-please
```

Change it to something long and random, for example:
```
- JWT_SECRET=MyZooStore2024SuperSecretKey!
```

Save and exit: press **Ctrl+X**, then **Y**, then **Enter**.

---

## Step 8 — Build and Start the App

This one command builds the containers and starts everything:

```bash
docker compose up --build -d
```

> - `--build` — builds the containers fresh from the code
> - `-d` — runs in the background ("detached") so your terminal stays free

The first run takes **3–5 minutes** while it downloads dependencies and builds the React app.
Subsequent starts are much faster.

Watch the progress:

```bash
docker compose logs -f
```

Press **Ctrl+C** to stop watching the logs (the app keeps running).

---

## Step 9 — Verify It's Running

Check that both containers are running:

```bash
docker compose ps
```

You should see two services — `frontend` and `backend` — both with status `Up`.

---

## Step 10 — Access the Website

Open a browser and go to:

```
http://<YOUR_MACHINE_IP>:3000
```

To find your machine's IP address, run:

```bash
hostname -I
```

Use the first IP address shown.

**Example:** If your IP is `10.2.10.50`, visit `http://10.2.10.50:3000`

You should see the Wild Kingdom Zoo Store home page!

---

## Step 11 — Log In

Use one of the built-in demo accounts:

| Role     | Username  | Password      |
|----------|-----------|---------------|
| Admin    | `admin`   | `admin123`    |
| Customer | `johndoe` | `password123` |

Or click **Sign Up** to create a new account.

---

## Daily Operations

### Stop the app
```bash
docker compose down
```

### Start it again (after stopping)
```bash
docker compose up -d
```

### Restart after code changes
```bash
docker compose up --build -d
```

### View live logs
```bash
docker compose logs -f
```

### View just backend logs
```bash
docker compose logs backend -f
```

---

## Troubleshooting

### "Connection refused" when visiting the site
- Check containers are running: `docker compose ps`
- Check logs for errors: `docker compose logs`
- Make sure you're using port 3000, not 80

### "Port already in use" error
Something else is using port 3000 or 5000. Find what's using it:
```bash
sudo ss -tlnp | grep 3000
```
Stop that process, or change the port in `docker-compose.yml`.

### App loads but login fails
- Make sure the backend container is running: `docker compose ps`
- Check backend logs: `docker compose logs backend`

### Need to reset all data (fresh start)
This deletes the database and starts clean:
```bash
docker compose down -v
docker compose up --build -d
```
> **Warning:** This deletes all users, orders, and data. The demo accounts will be re-created.

### Check how much disk space Docker is using
```bash
docker system df
```

---

## File Structure Reference

```
zoo-store/
├── backend/          ← Node.js API server
│   ├── server.js
│   ├── database.js   ← SQLite setup & seed data
│   └── routes/       ← auth, products, cart, orders, admin
├── frontend/         ← React website
│   └── src/
│       ├── pages/    ← Home, Shop, Cart, Checkout, Admin...
│       └── context/  ← Login state, Cart state
├── docker-compose.yml ← Starts everything together
└── DEPLOY.md         ← This file
```

The database file is stored in a Docker volume called `zoo_data` and persists across
restarts automatically.
