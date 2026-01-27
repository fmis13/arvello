# Task Completion Checklist

Before considering a task complete, ensure the following:

## 1. Code Quality
- [ ] Code follows the project's style conventions.
- [ ] No unused imports or variables.
- [ ] Proper error handling is implemented.

## 2. Testing
- [ ] All existing tests pass: `python manage.py test`.
- [ ] New tests are added for new features or bug fixes.
- [ ] Manual verification of the changes in the browser.

## 3. Documentation
- [ ] Update relevant documentation in `docs/` if necessary.
- [ ] Create a spec/analysis doc for non-trivial changes.

## 4. UI/UX (if applicable)
- [ ] Changes are responsive and work on mobile.
- [ ] Accessibility standards are maintained (ARIA labels, focus management).
- [ ] Design tokens are used for styling.

## 5. Database
- [ ] Migrations are created and tested if models were changed.
