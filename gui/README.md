# Kalavai-gui


# Welcome to Reflex!

> Template: https://github.com/reflex-dev/templates/tree/main/dashboard


Run with:

```bash
conda create --name reflex
conda activate reflex
pip install -r requirements.txt
reflex run

App running at: http://localhost:3000
Backend running at: http://0.0.0.0:8000
```

## About this Template

This template has the following directory structure:

```bash
├── README.md
├── assets
├── rxconfig.py
└── dashboard
    ├── __init__.py
    ├── components
    │   ├── __init__.py
    │   ├── navbar.py
    │   └── sidebar.py
    ├── pages
    │   ├── __init__.py
    │   ├── about.py
    │   ├── index.py
    │   ├── profile.py
    │   ├── settings.py
    │   └── table.py
    ├── styles.py
    ├── templates
    │   ├── __init__.py
    │   └── template.py
    └── {your_app}.py
```

See the [Project Structure docs](https://reflex.dev/docs/getting-started/project-structure/) for more information on general Reflex project structure.

### Adding Pages

In this template, the pages in your app are defined in `{your_app}/pages/`.
Each page is a function that returns a Reflex component.
For example, to edit this page you can modify `{your_app}/pages/index.py`.
See the [pages docs](https://reflex.dev/docs/pages/routes/) for more information on pages.

In this template, instead of using `rx.add_page` or the `@rx.page` decorator,
we use the `@template` decorator from `{your_app}/templates/template.py`.

To add a new page:

1. Add a new file in `{your_app}/pages/`. We recommend using one file per page, but you can also group pages in a single file.
2. Add a new function with the `@template` decorator, which takes the same arguments as `@rx.page`.
3. Import the page in your `{your_app}/pages/__init__.py` file and it will automatically be added to the app.
4. Order the pages in `{your_app}/components/sidebar.py` and `{your_app}/components/navbar.py`.



## Build docker

docker build -t kalavai/kalavai-gui:latest .
docker push kalavai/kalavai-gui:latest

