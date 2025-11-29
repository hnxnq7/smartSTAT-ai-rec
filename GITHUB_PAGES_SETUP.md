# Fix GitHub Pages - Deploy Next.js App Instead of README

If GitHub Pages is showing your README instead of your Next.js app, follow these steps:

## Step 1: Enable GitHub Actions for Pages

1. Go to your repository on GitHub
2. Click **Settings** (top menu)
3. Scroll down to **Pages** (left sidebar)
4. Under **"Source"**, you'll see options like:
   - Deploy from a branch
   - GitHub Actions
   
5. **Select "GitHub Actions"** (NOT "Deploy from a branch")
6. Save the changes

## Step 2: Verify Your Workflow File Exists

Make sure you have the workflow file at:
```
.github/workflows/deploy.yml
```

If it doesn't exist, the workflow I created should be in your repository. If not, create it with the content from the deploy.yml file.

## Step 3: Trigger the Workflow

1. Go to the **Actions** tab in your repository
2. You should see "Deploy to GitHub Pages" workflow
3. If it hasn't run yet:
   - Push any change to the `main` branch, OR
   - Go to Actions → "Deploy to GitHub Pages" → "Run workflow" (button on the right)

## Step 4: Wait for Deployment

1. Click on the workflow run to see progress
2. Wait for both jobs to complete:
   - ✅ **build** job (builds your Next.js app)
   - ✅ **deploy** job (deploys to GitHub Pages)
3. Once complete, your site will be live!

## Step 5: Check Your Site

Your site should be available at:
- `https://[your-username].github.io/[repository-name]`
- Or if it's your main site: `https://[your-username].github.io`

## Troubleshooting

### Still seeing README?

1. **Clear browser cache** - Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
2. **Check the Actions tab** - Make sure the workflow completed successfully
3. **Check the deploy job** - Look for any errors in the logs
4. **Verify the path** - The workflow uploads from `./out` folder

### Workflow fails?

1. Check that `npm run build` works locally
2. Verify all dependencies are in `package.json`
3. Check the workflow logs for specific error messages

### Site shows 404?

1. If your repo is NOT at root (e.g., `username.github.io/repo-name`):
   - Uncomment and set `basePath` in `next.config.js`:
   ```javascript
   basePath: '/smartSTAT',  // Replace with your repo name
   assetPrefix: '/smartSTAT',
   ```
   - Rebuild and push again

## Quick Fix Checklist

- [ ] Changed Pages source to "GitHub Actions" (not "Deploy from a branch")
- [ ] Workflow file exists at `.github/workflows/deploy.yml`
- [ ] Workflow has run successfully (check Actions tab)
- [ ] Cleared browser cache
- [ ] If repo is in subdirectory, set `basePath` in `next.config.js`

After completing these steps, your Next.js app should be live on GitHub Pages!

