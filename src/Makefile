install:
	pip install --upgrade pip &&\
		pip install -r requirements.txt

run-uvicorn:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

all: install

# Clear all Docker data
go-to-docker-dir:
	cd ../docker

stop-all-containers:
	@if [ -n "$$(docker ps -q)" ]; then docker stop $$(docker ps -q); fi

remove-all-containers:
	@if [ -n "$$(docker ps -aq)" ]; then docker rm $$(docker ps -aq); fi

remove-all-images:
	@if [ -n "$$(docker images -q)" ]; then docker rmi $$(docker images -q); fi

remove-all-volumes:
	@if [ -n "$$(docker volume ls -q)" ]; then docker volume rm $$(docker volume ls -q); fi

prune-all:
	docker system prune --all

# Clear all Docker data in one step
clear-docker: go-to-docker-dir stop-all-containers remove-all-containers remove-all-images remove-all-volumes prune-all

# Build and run Docker containers
run-service:
	docker compose -f '../docker/docker-compose.yml' up -d --build $(serviceName)

run-all-services:
	docker compose -f '../docker/docker-compose.yml' up -d --build

# Stop Docker containers
stop-service:
	docker stop $(serviceName)

stop-all-services:
	docker compose -f '../docker/docker-compose.yml' down

