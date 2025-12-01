# Cloud Run Deployment Guide

This guide walks through packaging the Streamlit command center into a Cloud Run service backed by the included Dockerfile.

## 1. Prerequisites
- **Google Cloud project** with billing enabled.
- **gcloud CLI** authenticated (`gcloud auth login`) and configured with the target project:
  ```bash
  export PROJECT_ID="gen-lang-client-0325928420"
  export REGION="us-central1"
  gcloud config set project "$PROJECT_ID"
  gcloud config set run/region "$REGION"
  ```
- **APIs enabled**:
  ```bash
  gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
  ```
- **Gemini / Google AI Studio API key** stored locally. You will provide it to Cloud Run via Secret Manager or environment variables.

## 2. Build the Container Image
The repository ships with a Cloud Run-ready `Dockerfile` that installs the project dependencies, the vendored Google ADK library, and launches Streamlit on port 8080.

```bash
# Submit the build to Cloud Build and push to Artifact Registry (Container Registry fallback also works).
gcloud builds submit --tag "gcr.io/${PROJECT_ID}/it-ops-streamlit:latest"
```

If you prefer Artifact Registry, create the repository first:
```bash
gcloud artifacts repositories create it-ops-repo \
  --repository-format=DOCKER \
  --location="$REGION" \
  --description="Container images for the IT Ops supervisor"

gcloud builds submit --tag "${REGION}-docker.pkg.dev/${PROJECT_ID}/it-ops-repo/it-ops-streamlit:latest"
```

## 3. Manage Secrets (Recommended)
Use Secret Manager to avoid embedding API keys in deployment commands:
```bash
echo -n "$GOOGLE_API_KEY" | gcloud secrets create it-ops-gemini-key --data-file=- --replication-policy=automatic
```
Grant the Cloud Run runtime service account access (replace with your runtime SA if different):
```bash
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
```
```bash
gcloud secrets add-iam-policy-binding it-ops-gemini-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```
(Replace the service account with the one you intend to use, for example a dedicated `cloud-run-it-ops@${PROJECT_ID}.iam.gserviceaccount.com`.)

## 4. Deploy to Cloud Run
Deploy the service, mapping the required environment variables and secrets.

```bash
gcloud run deploy it-ops-observability \
  --image "gcr.io/${PROJECT_ID}/it-ops-streamlit:latest" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars PYTHONPATH=/app/src \
  --set-env-vars STREAMLIT_SERVER_HEADLESS=true \
  --set-secrets GOOGLE_API_KEY=it-ops-gemini-key:latest \
  --cpu=1 \
  --memory=1Gi \
  --min-instances=0 \
  --max-instances=2
```

If you must pass the API key directly (not recommended), replace the `--set-secrets` flag with `--set-env-vars GOOGLE_API_KEY=your-key`.

## 5. Verify the Deployment
1. Retrieve the service URL:
   ```bash
   gcloud run services describe it-ops-observability --format='value(status.url)'
   ```
2. Open the URL in a browser. The Streamlit dashboard should render after the container cold-starts (~30s on first run).
3. Trigger a dashboard refresh or run the supervisor prompts to confirm Gemini access. Check Cloud Run logs if any errors appear:
   ```bash
   gcloud run services logs read it-ops-observability --limit=100
   ```

## 6. Updating the Service
After pushing new commits:
```bash
gcloud builds submit --tag "gcr.io/${PROJECT_ID}/it-ops-streamlit:latest"
gcloud run deploy it-ops-observability \
  --image "gcr.io/${PROJECT_ID}/it-ops-streamlit:latest" \
  --region "$REGION"
```
Cloud Run performs a rolling update with zero downtime.

## 7. Tearing Down
Delete the Cloud Run service and container image when the demo period ends:
```bash
gcloud run services delete it-ops-observability --region "$REGION"
gcloud container images delete "gcr.io/${PROJECT_ID}/it-ops-streamlit:latest" --force-delete-tags
```
If you created an Artifact Registry repository, delete it as well:
```bash
gcloud artifacts repositories delete it-ops-repo --location="$REGION"
```

## 8. Troubleshooting Tips
- **Quota or authentication errors:** Ensure the service account tied to Cloud Run has `roles/secretmanager.secretAccessor` (if using Secret Manager) and that the Gemini API key is valid.
- **Cold start latency:** Increase `--min-instances` to `1` for faster first-response at the expense of one always-on instance.
- **Large container build times:** Verify the `.dockerignore` excludes notebooks, screenshots, and test artifacts.
- **Streamlit CORS/XSRF issues:** The Dockerfile sets `STREAMLIT_SERVER_ENABLE_CORS=false` and enables XSRF protection; adjust via `--set-env-vars` if integrating behind a reverse proxy.

With these steps the Streamlit command center runs fully managed on Cloud Run, ready for demos or stakeholder walkthroughs.
