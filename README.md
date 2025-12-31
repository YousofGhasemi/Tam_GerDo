# Tam GerDo - Recipe Management API

A production-grade Django REST API built with Test-Driven Development (TDD), containerized with Docker, and configured for deployment with uWSGI and Nginx.

## Tech Stack

- **Framework:** Django 5.2.9, Django REST Framework 3.15.2
- **Database:** PostgreSQL 16.11
- **API Documentation:** drf-spectacular (OpenAPI/Swagger)
- **Authentication:** Token-based authentication
- **Image Processing:** Pillow
- **Server:** uWSGI (production), Django dev server (development)
- **Reverse Proxy:** Nginx
- **Containerization:** Docker, Docker Compose
- **Testing:** Django TestCase with 100% coverage
- **Linting:** Ruff
- **CI/CD:** GitHub Actions

## Project Structure

```
.
├── app/
│   ├── app/              # Django project settings
│   ├── core/             # Core models (User, Recipe, Tag, Ingredient)
│   ├── recipe/           # Recipe API endpoints
│   ├── user/             # User authentication API
│   └── manage.py
├── proxy/                # Nginx configuration
├── scripts/              # Deployment scripts
├── .github/workflows/    # CI/CD pipelines
└── docker-compose*.yml   # Docker configurations
```

## Features

- **User Management**
  - Custom user model with email authentication
  - Token-based authentication
  - User profile management
  - Users can mark recipes as favorites

- **Recipe Management**
  - CRUD operations for recipes
  - Image upload support
  - Recipe filtering by tags and ingredients
  - Price and time tracking

- **Tags & Ingredients**
  - Organize recipes with tags
  - Manage ingredients separately
  - Filter recipes by tags/ingredients

- **API Documentation**
  - Auto-generated OpenAPI/Swagger documentation
  - Interactive API browser

## Prerequisites

- Docker
- Docker Compose
- Git

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/YousofGhasemi/Tam_GerDo.git
cd Tam_GerDo
```

### 2. Create an environment file

```bash
cp .env.sample .env
```

Edit `.env` with your settings (optional for dev, defaults work):

```env
DB_NAME=devdb
DB_USER=devuser
DB_PASS=changeme
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_ALLOWED_HOSTS=127.0.0.1
```

### 3. Build and run with Docker Compose

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`

### 4. Run tests

```bash
docker compose run --rm app sh -c "python manage.py test"
```

### 5. Run linting

```bash
docker compose run --rm app sh -c "ruff check --fix --no-cache"
```

## API Endpoints

### Authentication
- `POST /api/user/create/` - Create new user
- `POST /api/user/token/` - Generate auth token
- `GET /api/user/me/` - Get/update user profile

### Recipes
- `GET /api/recipe/recipes/` - List recipes
- `POST /api/recipe/recipes/` - Create recipe
- `GET /api/recipe/recipes/{id}/` - Recipe detail
- `PATCH /api/recipe/recipes/{id}/` - Update recipe
- `DELETE /api/recipe/recipes/{id}/` - Delete recipe
- `POST /api/recipe/recipes/{id}/upload-image/` - Upload recipe image

### Favorite Recipes
- `GET /api/recipe/recipes/favorites/` - List user favorite recipes
- `POST /api/recipe/recipes/{id}/favorite/` - Add recipe to favorites
- `DELETE /api/recipe/recipes/{id}/favorite/` - Remove recipe from favorites
- 
### Tags
- `GET /api/recipe/tags/` - List tags
- `POST /api/recipe/tags/` - Create tag
- `GET /api/recipe/tags/{id}/` - Tag detail
- `PATCH /api/recipe/tags/{id}/` - Update tag
- `DELETE /api/recipe/tags/{id}/` - Delete tag

### Ingredients
- `GET /api/recipe/ingredients/` - List ingredients
- `POST /api/recipe/ingredients/` - Create ingredient
- `GET /api/recipe/ingredients/{id}/` - Ingredient detail
- `PATCH /api/recipe/ingredients/{id}/` - Update ingredient
- `DELETE /api/recipe/ingredients/{id}/` - Delete ingredient

### Documentation
- `GET /api/docs/` - Swagger UI

## Production Deployment

### 1. Prepare environment variables

Create `.env` file with production values:

```env
DB_NAME=production_db
DB_USER=production_user
DB_PASS=strong_password_here
DJANGO_SECRET_KEY=production-secret-key-min-50-chars
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

⚠️ **Important:** Use strong, unique values for production. Never use default values like `changeme`.

### 2. Deploy with Docker Compose

```bash
docker compose -f docker-compose-deploy.yml up --build -d
```

This configuration:
- Uses uWSGI with 4 worker processes
- Serves static/media files through Nginx
- Runs PostgreSQL in a separate container
- Automatically restarts on failure
- Exposes port 8000

### 3. Collect static files (first time only)

```bash
docker compose -f docker-compose-deploy.yml exec app sh -c "python manage.py collectstatic --noinput"
```

### 4. Create superuser

```bash
docker compose -f docker-compose-deploy.yml exec app sh -c "python manage.py createsuperuser"
```

## CI/CD Pipeline

GitHub Actions automatically runs on every push:

1. **Build** - Builds Docker image
2. **Test** - Runs full test suite
3. **Lint** - Checks code quality with Ruff

Workflow requires these GitHub secrets:
- `DOCKERHUB_USER`
- `DOCKERHUB_TOKEN`

## Development Workflow

### Running management commands

```bash
docker compose run --rm app sh -c "python manage.py <command>"
```

### Accessing Django shell

```bash
docker compose run --rm app sh -c "python manage.py shell"
```

### Database migrations

```bash
# Create migrations
docker compose run --rm app sh -c "python manage.py makemigrations"

# Apply migrations
docker compose run --rm app sh -c "python manage.py migrate"
```

### Stopping services

```bash
docker compose down
```

### Removing volumes (⚠️ deletes database)

```bash
docker compose down -v
```

## Testing Strategy

This project follows Test-Driven Development (TDD):

- **Unit Tests:** Model methods and custom commands
- **Integration Tests:** API endpoints with authentication
- **Test Coverage:** All models, views, and serializers
- **Test Database:** Separate PostgreSQL container for tests

Run specific test modules:

```bash
# Test specific app
docker compose run --rm app sh -c "python manage.py test core"

# Test specific file
docker compose run --rm app sh -c "python manage.py test core.tests.test_models"

# Verbose output
docker compose run --rm app sh -c "python manage.py test --verbosity 2"
```

## Common Issues

### Port 8000 already in use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Database connection issues

```bash
# Check if database is ready
docker compose logs db

# Restart database
docker compose restart db
```

### Permission errors in volumes

```bash
# Fix volume permissions
docker compose down -v
docker compose up --build
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`docker compose run --rm app sh -c "python manage.py test"`)
5. Run linting (`docker compose run --rm app sh -c "ruff check --fix"`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the terms specified in the LICENSE file.

## Contact

**Maintainer:** GoYousef.com

For issues and questions, please open an issue on GitHub.
