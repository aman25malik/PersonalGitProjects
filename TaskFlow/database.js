const sqlite3 = require('sqlite3').verbose();
const path = require('path');

// Path to your SQLite database file
const dbPath = path.resolve(__dirname, 'TaskFlowDB.db');

// Create a new SQLite3 database connection
const db = new sqlite3.Database(dbPath, (err) => {
  if (err) {
    console.error('Error opening database:', err.message);
  } else {
    console.log('Connected to the SQLite3 database.');
  }
});

// Function to close the database connection
const close = () => {
  db.close((err) => {
    if (err) {
      console.error('Error closing database:', err.message);
    } else {
      console.log('Database connection closed.');
    }
  });
};

module.exports = {
  db,
  close
};