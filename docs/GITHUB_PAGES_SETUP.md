# GitHub Pages Setup Guide

This guide explains how to publish the GC-Forged-Pylot landing page on GitHub Pages.

## Quick Setup

1. **Go to Repository Settings**
   - Navigate to your GitHub repository
   - Click on "Settings" tab
   - Scroll down to "Pages" section in the left sidebar

2. **Configure GitHub Pages**
   - Under "Source", select the branch you want to deploy (typically `main`)
   - Select "/ (root)" as the folder
   - Click "Save"

3. **Wait for Deployment**
   - GitHub will automatically build and deploy your site
   - This usually takes 1-2 minutes
   - You'll see a notification with the URL once it's ready

4. **Access Your Landing Page**
   - Your site will be available at: `https://[username].github.io/[repository-name]/`
   - For example: `https://NickScherbakov.github.io/GC-Forged-Pylot/`

## Custom Domain (Optional)

If you want to use a custom domain:

1. Add a `CNAME` file to the repository root with your domain name
2. Configure your domain's DNS settings to point to GitHub Pages
3. Update the GitHub Pages settings to use your custom domain

## Updating the Landing Page

The landing page is located at `index.html` in the repository root. Any changes pushed to the configured branch will automatically trigger a new deployment.

## Features of the Landing Page

The landing page includes:

- **Hero Section**: Eye-catching introduction with clear value proposition
- **Features Grid**: Six key capabilities with icons and descriptions
- **Code Examples**: Practical usage demonstrations
- **Architecture Visualization**: System workflow diagram
- **Philosophy Section**: The "Egg" concept explanation
- **Getting Started**: Three-step quickstart guide
- **Use Cases**: Real-world applications
- **Community Section**: Contribution opportunities
- **Footer**: Links to documentation and resources

## Customization

To customize the landing page:

1. Edit `index.html` directly
2. Modify colors by changing CSS variables in the `:root` section
3. Update content sections as needed
4. Commit and push changes to trigger redeployment

## Troubleshooting

**Page not updating?**
- Check the Actions tab to see if the deployment succeeded
- Clear your browser cache
- Wait a few minutes for CDN propagation

**404 Error?**
- Ensure `index.html` is in the correct location (root or docs folder)
- Verify the GitHub Pages source settings are correct
- Check that the branch contains the latest changes

**Styling issues?**
- Check browser console for errors
- Ensure CSS is inline in the HTML file (as it is in the current setup)
- Test locally first using `python -m http.server 8080`

## Local Development

To preview the landing page locally:

```bash
# Start a simple HTTP server
python -m http.server 8080

# Open in browser
# Navigate to http://localhost:8080/index.html
```

## Design Philosophy

The landing page follows these principles:

- **Informative yet concise**: Conveys the project's power without overwhelming details
- **Narrative style**: Tells a story about autonomous AI evolution
- **Subtle persuasion**: Encourages contribution through intelligent, non-pushy messaging
- **Professional aesthetics**: Modern dark theme with gradient accents
- **Responsive design**: Works seamlessly on desktop, tablet, and mobile
- **Performance-first**: Self-contained with no external dependencies

## Analytics (Optional)

To add analytics to track visitor behavior:

1. Sign up for a service like Google Analytics or Plausible
2. Add the tracking code to the `<head>` section of `index.html`
3. Commit and deploy

## Maintenance

Regular maintenance tasks:

- Update statistics and metrics as the project grows
- Add new features to the feature grid
- Refresh code examples with latest best practices
- Update links if documentation structure changes
- Review and respond to feedback from visitors

---

For questions about GitHub Pages, visit the [official documentation](https://docs.github.com/en/pages).
