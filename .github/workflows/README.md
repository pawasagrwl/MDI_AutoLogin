# GitHub Actions Workflows

## Build Workflow

The `build.yml` workflow automatically builds the Windows EXE when:

1. **Tag Push**: When you push a tag starting with `v` (e.g., `v1.0.0`), it will:
   - Build the EXE
   - Create a GitHub Release
   - Attach the EXE to the release

2. **Manual Trigger**: You can manually trigger the build from the Actions tab:
   - Go to Actions → Build Windows EXE → Run workflow
   - Optionally specify a version (e.g., `v1.0.0`)
   - The EXE will be available as a downloadable artifact

## How to Create a Release

### Option 1: Using Git Tags (Recommended)

```bash
# Create and push a tag
git tag v1.0.0
git push origin v1.0.0
```

This will automatically:
- Trigger the build
- Create a GitHub Release
- Attach the EXE

### Option 2: Manual Workflow Dispatch

1. Go to your repository on GitHub
2. Click on "Actions" tab
3. Select "Build Windows EXE" workflow
4. Click "Run workflow"
5. Optionally enter a version (e.g., `v1.0.0`)
6. Click "Run workflow"
7. Wait for the build to complete
8. Download the EXE from the artifacts

## Testing the Workflow

Before creating your first release, test the workflow:

1. Push the workflow file to your repository
2. Go to Actions tab
3. Manually trigger the workflow
4. Verify the build succeeds
5. Download and test the EXE artifact

Once confirmed working, you can use tags to create releases automatically.

