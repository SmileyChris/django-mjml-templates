# Releasing

1. Bump `version` in `pyproject.toml`.
2. Add a `## X.Y.Z (YYYY-MM-DD)` section to `CHANGELOG.md`.
3. Commit and push to `main`; wait for CI to pass.
4. Tag and push:

   ```sh
   git tag vX.Y.Z && git push origin vX.Y.Z
   ```

The `Release` workflow builds the package, publishes it to PyPI via trusted publishing
(the `pypi` environment, restricted to `v*` tags), then creates a GitHub Release with
the matching `CHANGELOG.md` section as notes and the built files attached.
