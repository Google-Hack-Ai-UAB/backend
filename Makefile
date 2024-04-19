
PHONY: stop remove build up migrate connect build-force pull down deploy

stop:
	docker stop backend

remove:
	docker remove backend

build:
	docker compose build 

build-force:
	docker compose build --no-cache

down:
	docker compose down

pull:
	docker compose pull

up:
	docker compose up -d
