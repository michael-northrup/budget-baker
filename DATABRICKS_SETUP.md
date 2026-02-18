# Databricks Asset Bundle CI/CD Setup Guide

This guide walks you through setting up automated deployments to Databricks using Asset Bundles and GitHub Actions.

## Prerequisites

1. **Databricks Workspace**: You need access to a Databricks workspace
2. **GitHub Repository**: Your code is already in GitHub
3. **Databricks CLI**: Install locally for testing
4. **Docker**: For local container testing (already installed)

## Step 1: Install Databricks CLI Locally

```bash
# macOS
brew tap databricks/tap
brew install databricks

# Or use curl
curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

# Verify installation
databricks --version
```

## Step 2: Configure Databricks Authentication

### Option A: OAuth (Recommended for development)
```bash
databricks configure --host https://your-workspace.cloud.databricks.com
```

### Option B: Personal Access Token
1. Go to Databricks workspace → User Settings → Access Tokens
2. Generate new token
3. Configure CLI:
```bash
databricks configure --token
# Enter your workspace URL and token when prompted
```

## Step 3: Set Up GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

### Required Secrets:
- `DATABRICKS_HOST`: Your workspace URL (e.g., `https://your-workspace.cloud.databricks.com`)
- `DATABRICKS_TOKEN`: Your personal access token or service principal token

### Optional (for production):
- `SERVICE_PRINCIPAL_NAME`: Service principal for production deployments
- `WAREHOUSE_ID`: SQL Warehouse ID for compute

### How to add secrets:
1. Go to your GitHub repo: https://github.com/michael-northrup/budget-baker
2. Settings → Secrets and variables → Actions → New repository secret
3. Add each secret name and value

## Step 4: Understanding the Bundle Structure

```
budget-baker/
├── databricks.yml          # Main bundle configuration
├── resources/
│   └── app.yml            # App resource definitions
├── .github/
│   └── workflows/
│       └── databricks-deploy.yml  # CI/CD pipeline
└── [your app files]
```

### Key Concepts:

**Targets**: Different deployment environments (dev, staging, prod)
- `dev`: Development environment (default)
- `staging`: Pre-production testing
- `prod`: Production environment

**Mode**:
- `development`: Allows rapid iteration, resources are prefixed with user email
- `production`: Stricter validation, requires service principal

## Step 5: Test Bundle Locally

```bash
# Validate the bundle
databricks bundle validate -t dev

# Deploy to dev (dry run)
databricks bundle deploy -t dev --dry-run

# Actually deploy to dev
databricks bundle deploy -t dev

# Check deployment status
databricks bundle summary -t dev
```

## Step 6: Set Up GitHub Environments (Optional but Recommended)

Create protected environments for staging and production:

1. Go to Settings → Environments
2. Create environments: `dev`, `staging`, `production`
3. For `production`:
   - Add required reviewers (yourself or team)
   - Add deployment branch rule (only `main`)
   - Add wait timer (e.g., 5 minutes)

## Step 7: Deployment Workflow

### Automatic Deployments:

1. **Push to `develop` branch** → Deploys to `dev` environment
2. **Push to `main` branch** → Deploys to `staging` environment
3. **Manual trigger** → Deploy to `prod` (requires approval if environment protection is set)

### Manual Production Deployment:

1. Go to Actions tab in GitHub
2. Select "Databricks Asset Bundle CI/CD" workflow
3. Click "Run workflow"
4. Select `prod` environment
5. Approve deployment (if environment protection is enabled)

## Step 8: Monitoring Deployments

### GitHub Actions:
- Check the Actions tab for build/deploy status
- View logs for each step
- See deployment summaries

### Databricks:
```bash
# List deployed resources
databricks bundle resources list -t dev

# View app logs
databricks apps logs budget-baker-dev

# Get app URL
databricks apps get budget-baker-dev
```

## CI/CD Pipeline Stages

The GitHub Actions workflow includes:

1. **Validate**:
   - Runs on all PRs and pushes
   - Installs dependencies with `uv`
   - Runs tests
   - Validates Databricks bundle syntax

2. **Deploy to Dev**:
   - Triggers on push to `develop` branch
   - Deploys to dev environment
   - Quick feedback for developers

3. **Deploy to Staging**:
   - Triggers on push to `main` branch
   - Pre-production testing environment
   - Validates before production

4. **Deploy to Production**:
   - Manual trigger only
   - Requires approval (if configured)
   - Creates git tag for tracking
   - Production-grade deployment

## Common Commands

```bash
# Validate bundle configuration
databricks bundle validate

# Deploy to specific target
databricks bundle deploy -t dev
databricks bundle deploy -t staging
databricks bundle deploy -t prod

# Destroy deployed resources
databricks bundle destroy -t dev

# Run a specific resource
databricks bundle run budget_baker_app -t dev

# View bundle schema
databricks bundle schema
```

## Troubleshooting

### Authentication Issues
```bash
# Check current authentication
databricks auth describe

# Re-authenticate
databricks configure --token
```

### Bundle Validation Errors
```bash
# Get detailed validation errors
databricks bundle validate -t dev --verbose

# Check bundle schema
databricks bundle schema
```

### Deployment Failures
- Check GitHub Actions logs for detailed error messages
- Verify secrets are set correctly in GitHub
- Ensure Databricks workspace permissions are correct
- Check that SQL Warehouse exists (if specified)

## Learning Resources

- [Databricks Asset Bundles Documentation](https://docs.databricks.com/dev-tools/bundles/index.html)
- [Databricks Apps Documentation](https://docs.databricks.com/apps/index.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Databricks CLI Reference](https://docs.databricks.com/dev-tools/cli/index.html)

## Next Steps

1. Install Databricks CLI
2. Configure authentication
3. Add GitHub secrets
4. Test bundle deployment locally
5. Push to `develop` branch to trigger first deployment
6. Monitor the GitHub Actions workflow
7. Access your deployed app in Databricks

## Production Checklist

Before deploying to production:
- [ ] Set up service principal for production deployments
- [ ] Configure GitHub environment protection rules
- [ ] Test in staging environment thoroughly
- [ ] Set up monitoring and alerting
- [ ] Document rollback procedures
- [ ] Review security and access controls
- [ ] Add cost monitoring/budgets
