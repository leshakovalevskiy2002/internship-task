## Environment setup

Before starting the application, create the environment file from the
appropriate example:

### Development

**cp .env.dev.example .env.dev**

Start the development environment:

**docker compose --env-file .env.dev up --build -d**

### Production

**cp .env.prod.example .env.prod**

Set the production credentials and other secrets in .env.prod.

Start the production environment:

**docker compose --env-file .env.prod --file docker-compose.prod.yml up --build -d**

## API documentation

After starting the development environment, the interactive API documentation is available at:

http://127.0.0.1:8000/docs

For the production environment, the API is available through Nginx at:

http://127.0.0.1/docs

The production URL should be replaced with the actual server hostname or domain when accessing the API remotely.
