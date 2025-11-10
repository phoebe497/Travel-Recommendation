# Contributing to Travel Recommendation System

Thank you for your interest in contributing to the Travel Recommendation System! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Your environment (PHP version, MongoDB version, OS)
- Any relevant error messages or logs

### Suggesting Enhancements

We welcome suggestions! Please create an issue with:
- A clear description of the enhancement
- Use cases for the feature
- Potential implementation approach (optional)
- Any relevant examples or mockups

### Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/phoebe497/Travel-Recommendation.git
   cd Travel-Recommendation
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**
   ```bash
   composer install
   php artisan test
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: your feature description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Provide a clear description of changes
   - Reference any related issues
   - Include screenshots for UI changes

## Code Style Guidelines

### PHP Code Style
- Follow PSR-12 coding standard
- Use type hints where possible
- Document all public methods with PHPDoc
- Keep methods focused and single-purpose

Example:
```php
/**
 * Generate daily recommendations for a user
 *
 * @param User $user The user to generate recommendations for
 * @param Carbon $date The date to generate recommendations
 * @return Recommendation The generated recommendation
 */
public function generateDailyRecommendations(User $user, Carbon $date): Recommendation
{
    // Implementation
}
```

### Naming Conventions
- Classes: PascalCase (e.g., `RecommendationService`)
- Methods: camelCase (e.g., `generateRecommendations`)
- Variables: camelCase (e.g., `$userId`)
- Constants: UPPER_SNAKE_CASE (e.g., `MAX_TOURS_PER_DAY`)

### File Structure
- Models: `app/Models/`
- Controllers: `app/Http/Controllers/`
- Services: `app/Services/`
- Tests: `tests/Feature/` or `tests/Unit/`

## Testing Guidelines

### Writing Tests
- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names

Example:
```php
public function test_recommendations_can_be_generated_for_user(): void
{
    $user = User::factory()->create();
    // Test implementation
}
```

### Running Tests
```bash
# Run all tests
php artisan test

# Run specific test file
php artisan test tests/Feature/RecommendationTest.php

# Run with coverage
php artisan test --coverage
```

## Documentation

### Required Documentation
- Update README.md for major features
- Add API documentation for new endpoints
- Include code comments for complex logic
- Update CHANGELOG.md with your changes

### Documentation Style
- Use clear, concise language
- Include code examples
- Add diagrams for complex features
- Keep examples up-to-date

## Development Setup

### Prerequisites
- PHP 8.1+
- MongoDB 4.0+
- Composer

### Setup Steps
```bash
# Clone repository
git clone https://github.com/phoebe497/Travel-Recommendation.git
cd Travel-Recommendation

# Install dependencies
composer install

# Copy environment file
cp .env.example .env

# Generate application key
php artisan key:generate

# Set up MongoDB (see MONGODB_SETUP.md)

# Seed database
php artisan db:seed

# Run tests
php artisan test
```

## Areas for Contribution

We especially welcome contributions in these areas:

### High Priority
- [ ] User authentication system (JWT/Passport)
- [ ] Rate limiting for API endpoints
- [ ] Enhanced test coverage
- [ ] Performance optimizations
- [ ] Security improvements

### Medium Priority
- [ ] Machine learning integration for preference learning
- [ ] Weather API integration
- [ ] Real-time traffic data
- [ ] Email notifications
- [ ] Admin dashboard UI

### Low Priority
- [ ] Multi-language support
- [ ] Currency conversion
- [ ] Social features (reviews, sharing)
- [ ] Mobile app integration examples
- [ ] Advanced analytics

## Commit Message Guidelines

Use conventional commit format:

```
type(scope): subject

body (optional)

footer (optional)
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```
feat(recommendation): add weather-based tour filtering

Add ability to filter tours based on weather conditions
using OpenWeather API integration.

Closes #123
```

```
fix(api): correct tour distance calculation

Fix Haversine formula implementation to properly
calculate distances between coordinates.
```

## Code Review Process

All submissions require review before merging:

1. **Automated Checks**
   - Tests must pass
   - Code style must comply with PSR-12
   - No merge conflicts

2. **Manual Review**
   - Code quality and maintainability
   - Documentation completeness
   - Test coverage
   - Security considerations

3. **Approval**
   - At least one maintainer approval required
   - All review comments addressed

## Questions?

- Create an issue for general questions
- Use discussions for broader topics
- Check existing documentation first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to Travel Recommendation System! 🎉
