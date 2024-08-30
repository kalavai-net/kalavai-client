# Documentation for Kalavai-cloud

## Install and build

```bash
virtualenv -p python3 env
source env/bin/activate
pip install -r requirements.txt
```

## Contribute to the docs

Add icons: https://squidfunk.github.io/mkdocs-material/reference/icons-emojis/?h=icons#with-colors-mkdocsyml

### Test changes

Run locally:
```bash
mkdocs serve
```

### Build docs to GitHub pages:

```bash
mkdocs gh-deploy
```

This will push a PR to the gh-pages branch, which can be approved / merged. Once it is, the new changes will be published at https://kalavai-net.github.io/kalavai-docs/



