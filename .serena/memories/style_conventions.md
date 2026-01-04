# Style and Conventions

## Backend (Python/Django)
- **Framework**: Django 5.1.4
- **Python Version**: 3.11+
- **Coding Style**: Follow PEP 8.
- **Naming**: Use `snake_case` for variables, functions, and methods. Use `PascalCase` for classes.
- **Type Hints**: Use type hints where possible for better clarity and IDE support.
- **Docstrings**: Use docstrings for complex functions and classes.

## Frontend (HTML/CSS/JS)
- **Framework**: Bootstrap 5.3.3
- **CSS**: Use CSS custom properties (design tokens) defined in `design-tokens.css`.
- **Layout**: Use Flexbox and Bootstrap's grid system.
- **Accessibility**: Follow WCAG 2.1 AA guidelines. Use semantic HTML, ARIA labels, and skip links.
- **Icons**: Use Material Symbols Outlined.
- **Fonts**: Inter font family.

## Database
- **Local**: SQLite (`db.sqlite3`)
- **Production**: PostgreSQL

## Project Structure
- `arvello/`: Main Django project and apps.
- `arvelloapp/`: Core application logic and templates.
- `arvello_fiscal/`: Fiscalization logic.
- `static/`: CSS, JS, and images.
- `docs/`: Project documentation and subagent specs.
