# Email Ingestion Setup Guide

## Step 1: Create Environment File

Create a `.env` file in your project root directory with the following content:

```bash
# Microsoft Graph API Configuration
GRAPH_TENANT_ID=your_tenant_id_here
GRAPH_CLIENT_ID=your_client_id_here
GRAPH_CLIENT_SECRET=your_client_secret_here

# Email Configuration
SHARED_MAILBOX=your_email@domain.com
MAILBOX_FOLDER=Inbox

# AWS S3 Configuration (optional)
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-2
S3_BUCKET=your-s3-bucket-name-here

# OpenAI Configuration (for future use)
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
SQLITE_DB_PATH=./data/intake.db
```

## Step 2: Microsoft Graph API Setup

### 2.1 Create Azure App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Fill in the details:
   - **Name**: `Email Ingestion App` (or any name you prefer)
   - **Supported account types**: Choose based on your needs
   - **Redirect URI**: Leave blank for now
5. Click **Register**

### 2.2 Configure API Permissions

1. In your new app registration, go to **API permissions**
2. Click **Add a permission**
3. Select **Microsoft Graph**
4. Choose **Application permissions**
5. Add these permissions:
   - `Mail.Read`
   - `Mail.ReadWrite`
   - `Mail.ReadBasic`
6. Click **Add permissions**
7. Click **Grant admin consent** (requires admin privileges)

### 2.3 Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Add a description and choose expiration
4. Click **Add**
5. **IMPORTANT**: Copy the secret value immediately (you won't see it again)

### 2.4 Get Your Credentials

1. **Tenant ID**: Copy from the **Overview** page
2. **Client ID**: Copy from the **Overview** page (Application ID)
3. **Client Secret**: Use the value you copied in step 2.3

## Step 3: Update Your .env File

Replace the placeholder values in your `.env` file:

```bash
GRAPH_TENANT_ID=12345678-1234-1234-1234-123456789012
GRAPH_CLIENT_ID=87654321-4321-4321-4321-210987654321
GRAPH_CLIENT_SECRET=your_actual_secret_here
SHARED_MAILBOX=your_actual_email@yourdomain.com
```

## Step 4: Test the Configuration

Run the test script to verify everything is working:

```bash
python scripts/test_email_ingestion.py
```

You should see all tests pass:
```
🧪 Email Ingestion System Test Suite
==================================================
🔧 Testing Environment Configuration...
✅ All required environment variables are set

📦 Testing Module Imports...
✅ Settings module imported
✅ EmailProcessor imported
✅ S3EmailUploader imported

🔐 Testing Microsoft Graph Authentication...
✅ Authentication successful

☁️  Testing S3 Configuration...
⚠️  S3 not configured (missing: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET)
   S3 upload functionality will not be available

📁 Testing Directory Structure...
✅ Data directory ready: data\emails

==================================================
📊 Test Results: 4/5 tests passed
🎉 All tests passed! The system is ready to use.
```

## Step 5: Run Email Ingestion

Once the tests pass, you can start using the system:

```bash
# Test with a few emails first
python scripts/run_email_ingestion.py --max-emails 5

# Process emails from a specific folder
python scripts/run_email_ingestion.py --folder "providerbills" --max-emails 10

# Process more emails
python scripts/run_email_ingestion.py --max-emails 50
```

## Optional: S3 Setup

If you want to upload emails to S3:

### 5.1 Create S3 Bucket

1. Go to [AWS S3 Console](https://s3.console.aws.amazon.com/)
2. Click **Create bucket**
3. Choose a unique bucket name
4. Select your preferred region
5. Keep other settings as default
6. Click **Create bucket**

### 5.2 Create IAM User

1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. Click **Users** > **Add user**
3. Enter username: `email-ingestion-user`
4. Select **Programmatic access**
5. Click **Next**

### 5.3 Attach S3 Policy

1. Click **Attach existing policies directly**
2. Search for and select `AmazonS3FullAccess` (or create a custom policy with minimal permissions)
3. Click **Next** > **Create user**

### 5.4 Get Access Keys

1. Click on your new user
2. Go to **Security credentials** tab
3. Click **Create access key**
4. Select **Application running outside AWS**
5. Click **Next** > **Create access key**
6. Copy the **Access key ID** and **Secret access key**

### 5.5 Update .env File

Add your S3 credentials:

```bash
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-2
S3_BUCKET=your-bucket-name
```

### 5.6 Test S3 Upload

```bash
# Upload existing emails to S3
python scripts/run_email_ingestion.py --action upload

# Fetch and upload in one command
python scripts/run_email_ingestion.py --action both --max-emails 10
```

## Troubleshooting

### Common Issues

1. **"Authority configuration" error**
   - Check that `GRAPH_TENANT_ID` is correct
   - Verify the tenant ID format: `12345678-1234-1234-1234-123456789012`

2. **"Invalid client" error**
   - Verify `GRAPH_CLIENT_ID` is correct
   - Check that the app registration exists in Azure

3. **"Invalid client secret" error**
   - The client secret may have expired
   - Create a new client secret in Azure Portal

4. **"Insufficient privileges" error**
   - Admin consent may not have been granted
   - Contact your Azure admin to grant permissions

5. **"Mailbox not found" error**
   - Verify `SHARED_MAILBOX` email address is correct
   - Check that the app has access to the mailbox

### Getting Help

- Check the full documentation in `EMAIL_INGESTION_README.md`
- Run the test script to identify specific issues
- Verify all environment variables are set correctly
- Check Azure Portal for app registration status

## Next Steps

Once everything is working:

1. **Start with small batches**: Use `--max-emails 5` to test
2. **Monitor the output**: Check the console logs for any issues
3. **Verify data**: Check the `data/emails/` directory for downloaded emails
4. **Scale up**: Increase `--max-emails` as needed
5. **Set up automation**: Consider running the script on a schedule

The system is designed to be robust and handle errors gracefully, so don't worry if some emails fail to process - they'll be logged and you can investigate later. 