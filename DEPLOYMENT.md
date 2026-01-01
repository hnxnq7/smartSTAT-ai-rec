# Deploying to GitHub Pages

This guide explains how to deploy the smartSTAT AI Recommendations app to GitHub Pages.

## Prerequisites

- A GitHub repository
- GitHub Pages enabled in your repository settings

## Deployment Steps

### Option 1: Automatic Deployment with GitHub Actions (Recommended)

1. **Enable GitHub Pages in your repository:**
   - Go to your repository on GitHub
   - Click **Settings** → **Pages**
   - Under "Source", select **GitHub Actions**

2. **Push your code to the `main` branch:**
   ```bash
   git add .
   git commit -m "Configure for GitHub Pages"
   git push origin main
   ```

3. **The GitHub Action will automatically:**
   - Build your Next.js app as a static site
   - Deploy it to GitHub Pages
   - Your site will be available at: `https://[username].github.io/[repository-name]`

### Option 2: Manual Deployment

If you prefer to deploy manually:

1. **Build the static site:**
   ```bash
   npm run build
   ```

2. **The `out` folder will contain your static site**

3. **Push the `out` folder to the `gh-pages` branch:**
   ```bash
   git subtree push --prefix out origin gh-pages
   ```

## Important Notes

### Base Path Configuration

If your repository is **NOT** at the root of your GitHub Pages site (i.e., `username.github.io/repo-name`), you need to update the base path:

1. Open `next.config.js`
2. Uncomment and update these lines:
   ```javascript
   basePath: '/smartSTAT',  // Replace 'smartSTAT' with your repo name
   assetPrefix: '/smartSTAT',
   ```
3. Rebuild and redeploy

### If Your Repository is at Root

If your repository is named `username.github.io` (which serves at the root), you don't need to set a base path. The current configuration will work as-is.

## Troubleshooting

### Page shows blank or 404

- Check that GitHub Pages is enabled in repository settings
- Verify the base path is correct if using a subdirectory
- Check the GitHub Actions workflow logs for build errors

### Styles not loading

- Ensure `output: 'export'` is set in `next.config.js`
- Verify `images: { unoptimized: true }` is set
- Check that the `.nojekyll` file exists in the repository

### Build fails

- Check that all dependencies are listed in `package.json`
- Verify Node.js version compatibility (requires Node 18+)
- Check the GitHub Actions logs for specific errors

## Testing Locally

Before deploying, test the static export locally:

```bash
npm run build
npx serve out
```

Then visit `http://localhost:3000` to verify everything works.







