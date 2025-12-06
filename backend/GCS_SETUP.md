# Google Cloud Storage Setup Guide

This guide explains how to set up Google Cloud Storage (GCS) backup for quote file uploads.

## Overview

The system uses a **hybrid storage approach**:
- **Primary**: Local filesystem (`./uploads/quotes/{year}/{month}/`)
- **Backup**: Google Cloud Storage Nearline (cost-optimized cold storage)

GCS backup is **optional** - the system works perfectly with local storage only.

## Why Use GCS Backup?

- **Durability**: 99.999999999% (11 nines) data durability
- **Cost-effective**: Nearline storage at ~$0.010/GB/month
- **Automatic backup**: Files uploaded to GCS in background
- **Disaster recovery**: Protect against local drive failure
- **Low monthly cost**: ~$0.05-0.50/month for typical usage

## Setup Options

### Option 1: Using Google Workspace Account (Recommended)

If you have a Google Workspace account, you can use your existing credentials:

1. **Install Google Cloud SDK**
   ```bash
   # Download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate with your Workspace account**
   ```bash
   gcloud auth application-default login
   ```

3. **Create GCS project and bucket** (one-time setup)
   ```bash
   # Set your project ID
   gcloud config set project YOUR_PROJECT_ID

   # Create bucket with Nearline storage
   gsutil mb -c nearline -l us-central1 gs://blb3d-quote-files
   ```

4. **Update .env file**
   ```env
   GCS_ENABLED=true
   GCS_BUCKET_NAME=blb3d-quote-files
   GCS_PROJECT_ID=YOUR_PROJECT_ID
   # GCS_CREDENTIALS_PATH - leave commented out to use default credentials
   ```

### Option 2: Using Service Account (Alternative)

For more control or automated deployments:

1. **Create service account** in Google Cloud Console
   - Go to IAM & Admin > Service Accounts
   - Create new service account with "Storage Object Creator" role

2. **Download JSON key file**
   - Click on service account > Keys > Add Key > JSON
   - Save as `gcs-service-account.json` in backend directory

3. **Update .env file**
   ```env
   GCS_ENABLED=true
   GCS_BUCKET_NAME=blb3d-quote-files
   GCS_PROJECT_ID=YOUR_PROJECT_ID
   GCS_CREDENTIALS_PATH=./gcs-service-account.json
   ```

## Testing GCS Setup

Test your GCS configuration:

```python
from google.cloud import storage

# This will use your configured credentials
client = storage.Client(project='YOUR_PROJECT_ID')
bucket = client.bucket('blb3d-quote-files')

# Test upload
blob = bucket.blob('test/hello.txt')
blob.upload_from_string('Hello World!')
print(f"SUCCESS: Uploaded test file to {bucket.name}")

# Test download
content = blob.download_as_text()
print(f"Downloaded: {content}")

# Cleanup
blob.delete()
```

## Cost Estimates

**Nearline Storage Pricing:**
- Storage: $0.010/GB/month
- Upload: Free
- Download: $0.01/GB (only if you need to restore)

**Example Monthly Costs:**
- 5 GB of files: $0.05/month
- 50 GB of files: $0.50/month
- 500 GB of files: $5.00/month

## Security Best Practices

1. **Never commit credentials to git**
   - `gcs-service-account.json` is in `.gitignore`
   - Use environment variables for sensitive data

2. **Use least-privilege access**
   - Service account only needs "Storage Object Creator" role
   - No need for full admin access

3. **Enable bucket versioning** (optional but recommended)
   ```bash
   gsutil versioning set on gs://blb3d-quote-files
   ```

## Troubleshooting

### Authentication Error
```
google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials
```

**Solution:** Run `gcloud auth application-default login` or set `GCS_CREDENTIALS_PATH`

### Bucket Not Found
```
google.api_core.exceptions.NotFound: 404 GET https://storage.googleapis.com/storage/v1/b/blb3d-quote-files
```

**Solution:** Create the bucket first using `gsutil mb` command above

### Permission Denied
```
google.api_core.exceptions.Forbidden: 403 POST https://storage.googleapis.com/upload/storage/v1/b/blb3d-quote-files/o
```

**Solution:** Grant "Storage Object Creator" role to your account/service account

## Disabling GCS Backup

To run without GCS backup (local storage only):

1. Set in `.env`:
   ```env
   GCS_ENABLED=false
   ```

2. Restart the application

The system will log a warning that GCS is disabled, but will continue to work normally with local storage.
