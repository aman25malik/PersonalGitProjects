# TaskFlow Project

## Setup Guide

1. **Install Dependencies:**
   - Install Node.js, Docker, Python, SQLite, AWS CLI.

2. **Install Swagger Editor:**
   - Pull the Docker image:
     ```bash
     docker pull swaggerapi/swagger-editor
     ```
   - Run the Swagger Editor:
     ```bash
     docker run -d -p 8081:8080 swaggerapi/swagger-editor
     ```
   - Swagger Editor enables editing OpenAPI definitions.

3. **Install SQLite3 for Node.js:**
   - Install the SQLite3 package:
     ```bash
     npm install sqlite3
     ```

4. **Database Setup:**
   - Created an SQLite3 database named `TaskFlowDB.db`.

5. **Basic Testing:**
   - Start the Node.js application:
     ```bash
     node app.js
     ```
   - This should connect to port 3000.

## API Testing with cURL

1. **GET /tasks**
  ```bash
  curl http://localhost:3000/tasks
    ``` 
2. **POST /tasks** 
    ```bash
    curl -X POST http://localhost:3000/tasks -H "Content-Type: application/json" -d '{"title": "New Task", "description": "Task description"}'
    ```
3. **GET /tasks** (byID)
    ```bash 
    curl http://localhost:3000/tasks/:id
    ```
4. **PUT /tasks/** (byID)
    ```bash
    curl -X PUT http://localhost:3000/tasks/:id -H "Content-Type: application/json" -d '{"title": "Updated Task", "description": "Updated description"}'
    ```
5. **DELETE /tasks/** (byID)
    ```bash
    curl -X DELETE http://localhost:3000/tasks/:id
    ```





