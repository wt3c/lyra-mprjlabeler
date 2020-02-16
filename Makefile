initial:
	cp templa [200~template-settings-compose.ini settings.ini

run:
	docker-compose up -d

reload:
	docker-compose restart web celery_worker

down:
	docker-compose down



