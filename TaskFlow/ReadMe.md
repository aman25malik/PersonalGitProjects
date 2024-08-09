#### Setup Guide:

- install Node.js, Docker, Python, SQLite, AWS CLI

- install SwaggerEditor through docker: 
    - "docker pull swaggerapi/swagger-editor"
    - "docker run -d -p 8081:8080 swaggerapi/swagger-editor"
    (SwaggerEditor enables editing OpenAPI definitions)

npm install sqlite3


API definitions are defined with OpenAPI swagger. Utilize Prism to define your data models and automatically generate SQL queries for creating, reading, updating, and deleting records in the database.

Created a sqlite3 db TaskFlowDB.db

Basic testing:
node app.js
    -> should connect to port 3000

##CLI testing for app.js:
GET /tasks
curl http://localhost:3000/tasks

POST /tasks
curl -X POST http://localhost:3000/tasks -H "Content-Type: application/json" -d '{"title": "New Task", "description": "Task description"}'

GET /tasks/
curl http://localhost:3000/tasks/:id

PUT /tasks/
curl -X PUT http://localhost:3000/tasks/:id -H "Content-Type: application/json" -d '{"title": "Updated Task", "description": "Updated description"}'

DELETE /tasks/
curl -X DELETE http://localhost:3000/tasks/id