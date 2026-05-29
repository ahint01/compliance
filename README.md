# Compliance Checker

A small Django app that scans Git repositories for leaked secrets using [Gitleaks](https://github.com/gitleaks/gitleaks). Results are stored in SQLite and shown on a web dashboard. The project also demonstrates packaging with Docker, deploying to AWS (ECR, ECS, EC2), and CI/CD with GitHub Actions.

## Features

- **Web dashboard** — submit a public Git URL; the app clones the repo, runs Gitleaks, and displays the latest findings per repository.
- **Management command** — scan a local checkout without the web UI: `python manage.py scan_repo /path/to/repo`.
- **Docker image** — Python 3.11, Django, Git, and Gitleaks pre-installed.
- **Terraform** — AWS networking, EC2 host, and ECS service definitions under `terraform/`.
- **GitHub Actions** — build and push the image to ECR, then roll out a new ECS task definition on pushes to `main`.

## Prerequisites

- Python 3.11+
- [Gitleaks](https://github.com/gitleaks/gitleaks#installing) (for local development outside Docker)
- Git

## Local development

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) for the dashboard. Django admin is at [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) (create a superuser with `python manage.py createsuperuser`).

### Scan a local repository

```bash
python manage.py scan_repo /path/to/your/repo
```

### Run with Docker

```bash
docker build -t compliance-checker .
docker run --rm -p 8000:8000 compliance-checker
```

On first run inside the container, run migrations if you need a persistent database:

```bash
docker run --rm -p 8000:8000 compliance-checker python manage.py migrate
```

For a demo, the default SQLite file is created in the container filesystem.

## Project layout

```
compliance/           # Django project settings and URLs
app/                  # Models, views, scan logic, dashboard template
  scan_service.py     # Clone remote repo + run Gitleaks
  management/commands/scan_repo.py   # Local path scans
terraform/            # AWS infrastructure (VPC, EC2, ECS)
.github/workflows/    # ECR build + ECS deploy
Dockerfile
requirements.txt
```

## Deployment

### Terraform

Infrastructure lives in `terraform/`. Configure your AWS credentials, then:

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Review `variables.tf` for defaults (e.g. region `us-east-2`, project name `compliance-checker-demo`).

### GitHub Actions

The workflow in `.github/workflows/main.yml` expects these repository secrets (environment: `production`):

| Secret | Purpose |
|--------|---------|
| `AWS_ACCESS_KEY_ID` | Deploy credentials |
| `AWS_SECRET_ACCESS_KEY` | Deploy credentials |
| `AWS_REGION` | ECR / ECS region |
| `ECR_REPOSITORY` | Image repository name |
| `ECS_CLUSTER_NAME` | Target cluster |
| `ECS_SERVICE_NAME` | Service to update |

The workflow updates the ECS task family `compliance-checker-demo-task` and container `compliance-checker-demo-django-container` to match your Terraform setup.

## Security notes

This repo is intended as a **demonstration**. Before production use:

- Set `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` via environment variables.
- Do not commit `db.sqlite3` or scan output containing real secrets.
- Restrict who can trigger scans (cloning arbitrary URLs has cost and abuse implications).
- Use a managed database instead of SQLite for multi-instance deployments.

## License

Demonstration project — add a license if you plan to distribute or reuse it.
