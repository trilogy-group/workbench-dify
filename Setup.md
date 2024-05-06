## Local Setup

```bash
export DOCKER_BUILDKIT=1
cd docker
docker-compose down
docker-compose build
docker-compose up -d
docker-compose logs -f api
```