# Server

![Architecture]()

Build Status - Backend
-----------------------

|    DEV    |     QA    |    UAT    |   MASTER   |
|-----------|-----------|-----------|------------|
|[![Build Status]()]()|[![Build Status]()]()|[![Build Status]()]()|[![Build Status]()]()|


|  ENV       |    ADMIN    |
|------------|-----------|
|  DEV       |   |
|  QA        |   |
|  UAT       |   |
|  PROD      |   |


## Development Environment Setup

  |Package/Library/Framework | Version|
  |---|---|
  |Python| v3.8|
  |Django| v3.0|
  |Django REST| v3.10.3|
  |Elastic Search| v7.9.1|
  |Kibana| v7.9.1|


##### Command Reference

  Services Available : postgres, webserver, redis, celeryworker, elasticsearch, kibana

1. To start django webserver

        sh ./start_django.sh

2. To start celery worker

        sh ./start_worker.sh

3. To start elasticsearch & kibana

        sh ./start_elasticsearch.sh


##### Open the Admin site in browser:

Admin : [http://localhost:8000/admin](http://localhost:8000/admin)

##### Connect to Local DB with following credentials:

    DATABASE : db_name
    HOST : 127.0.0.1
    PORT : 5432
    USER : postgres
    PASSWORD : postgres

##### Open the SEIU API Docs in browser:

Swagger : [http://localhost:8000/swagger](http://localhost:8000/swagger)

##### Open the SEIU ElasticSearch & Kibana in browser:

ElasticSearch : [http://localhost:9200](http://localhost:9200)\
Kibana : [http://localhost:5601](http://localhost:5601)
