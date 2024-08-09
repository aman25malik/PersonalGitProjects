const express = require('express');
const { db, close } = require('./database');

const app = express();
app.use(express.json());

// Example route to get all tasks
app.get('/tasks', (req, res) => {
  db.all('SELECT * FROM Task', [], (err, rows) => {
    if (err) {
      throw err;
    }
    res.json(rows);
  });
});

// Example route to create a new task
app.post('/tasks', (req, res) => {
  const { title, description } = req.body;
  db.run('INSERT INTO Task (title, description) VALUES (?, ?)', [title, description], function(err) {
    if (err) {
      return console.error(err.message);
    }
    res.status(201).json({ id: this.lastID, title, description });
  });
});

// Example route to get a task by ID
app.get('/tasks/:id', (req, res) => {
  const id = req.params.id;
  db.get('SELECT * FROM Task WHERE id = ?', [id], (err, row) => {
    if (err) {
      throw err;
    }
    res.json(row);
  });
});

// Example route to update a task by ID
app.put('/tasks/:id', (req, res) => {
  const id = req.params.id;
  const { title, description } = req.body;
  db.run('UPDATE Task SET title = ?, description = ? WHERE id = ?', [title, description, id], function(err) {
    if (err) {
      return console.error(err.message);
    }
    res.json({ id, title, description });
  });
});

// Example route to delete a task by ID
app.delete('/tasks/:id', (req, res) => {
  const id = req.params.id;
  db.run('DELETE FROM Task WHERE id = ?', [id], function(err) {
    if (err) {
      return console.error(err.message);
    }
    res.status(204).end();
  });
});

// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});

// Close the database connection on server shutdown
process.on('SIGINT', () => {
  close();
  process.exit();
});