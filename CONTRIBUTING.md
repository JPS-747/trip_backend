# Contributing to Trippen

Thank you for your interest in contributing to Trippen! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Report inappropriate behavior to the maintainers

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 16+
- Git

### Setup Development Environment

1. **Fork the repository**

   ```bash
   git clone https://github.com/YOUR_USERNAME/trippen.git
   cd trippen
   ```

2. **Create a feature branch**

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Backend Setup**

   ```powershell
   python -m venv v310
   & .\v310\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

4. **Frontend Setup**
   ```powershell
   cd frontend-react
   npm install
   ```

## Development Workflow

### Making Changes

1. **Create a new branch** from `main`:

   ```bash
   git checkout -b feature/description-of-feature
   ```

2. **Make your changes** with clear, descriptive commits:

   ```bash
   git commit -m "feat: add new feature description"
   ```

3. **Test your changes thoroughly**
   - Backend: Run the API server and test endpoints
   - Frontend: Test the React components
   - Integration: Test backend and frontend together

### Backend Development

- **Code Style**: Follow PEP 8 guidelines
- **Type Hints**: Use Python type hints where possible
- **Comments**: Document complex logic with clear comments
- **Testing**: Write tests for new functionality

#### Running the Backend

```powershell
uvicorn api:api --reload
```

#### File Structure

- `api.py` - FastAPI routes and WebSocket endpoints
- `app.py` - Core business logic
- `db.py` - Database initialization
- Migration scripts in root for DB updates

### Frontend Development

- **Code Style**: Follow TypeScript/React conventions
- **Components**: Create reusable, well-documented components
- **Styling**: Use CSS modules or inline styles
- **Testing**: Test components in isolation

#### Running the Frontend

```powershell
cd frontend-react
npm run dev
```

## Commit Message Guidelines

Use clear, descriptive commit messages:

```
feat: add new feature
fix: resolve bug in component
docs: update API documentation
refactor: improve code structure
test: add unit tests for feature
chore: update dependencies
```

## Pull Request Process

1. **Update the README.md** with any new features or changes
2. **Test thoroughly** - both backend and frontend
3. **Create a Pull Request** with a clear description
4. **Link related issues** using `#issue_number`
5. **Fill out the PR template** completely
6. **Wait for review** and address feedback

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Changes tested locally
- [ ] PR description is clear and complete

## Reporting Issues

### Bug Reports

Use the bug report template and include:

- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Screenshots if applicable
- Environment details (OS, Python version, etc.)

### Feature Requests

Use the feature request template and include:

- Clear description of the feature
- Why you need it
- How it should work
- Any related issues

## Code Review

When reviewing code:

- Be constructive and respectful
- Ask questions if something is unclear
- Suggest improvements with explanations
- Approve when satisfied with the changes

## Documentation

All contributions should include updated documentation:

- **Code Comments**: Explain "why", not "what"
- **README Updates**: Document new features
- **Inline Docs**: Add docstrings to functions
- **API Docs**: Update FastAPI route documentation

## Testing

### Backend Testing

```powershell
# Validate Python syntax
python -m py_compile app.py api.py

# Run any existing tests
pytest (if applicable)
```

### Frontend Testing

```powershell
cd frontend-react
npm run lint (if configured)
npm run build (test production build)
```

## Performance Considerations

- Minimize database queries
- Use pagination for large datasets
- Optimize React components (avoid unnecessary re-renders)
- Cache data appropriately

## Security

- Never commit sensitive data (API keys, passwords, secrets)
- Validate all user inputs
- Use environment variables for configuration
- Follow FastAPI security best practices

## Project Structure Guidelines

```
trippen/
├── api.py           # API routes - keep focused
├── app.py           # Business logic - organize by feature
├── db.py            # Database layer
├── requirements.txt # Dependencies
└── frontend-react/  # Keep frontend separate
```

## Questions?

- Open an issue for questions
- Check existing issues for similar questions
- Review API documentation at `/docs`

## Recognition

Contributors will be recognized in:

- Pull request acknowledgments
- Release notes
- Project contributors list

## License

By contributing to Trippen, you agree that your contributions will be licensed under the MIT License.

---

Thank you for making Trippen better! 🎉
