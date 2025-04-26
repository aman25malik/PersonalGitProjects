const express = require('express');
const { PrismaClient } = require('@prisma/client');

const app = express();
const prisma = new PrismaClient();
app.use(express.json());

//GET all tasks
app.get('/tasks', async (req, res) => {
  try {
    const tasks = await prisma.task.findMany();
    res.json(tasks);
  } catch (error) {
    res.status(500).json({ error: 'Something went wrong' });
  }
});

//CREATE new task
app.post('/tasks', async (req, res) => {
  const { title, description } = req.body;
  try{
    const newTask = await prisma.task.create({
      data: {
        title: title,
        description: description
      }
    });
    res.status(201).json(newTask);
  }
  catch (error){
    res.status(500).json({ error: 'Something went wrong' });
  }
});

//GET task by ID
app.get('/tasks/:id', async (req, res) => {
  const taskId = parseInt(req.params.id, 10);
  try{
    const task = await prisma.task.findUnique({ where: {id: taskId}});
    res.status(200).json(task);
  }
  catch (error) {
    res.status(500).json({ error: 'Something went wrong' });
  }
  
});

//POST update task by ID
app.put('/tasks/:id', async (req, res) => {
  const taskId = parseInt(req.params.id, 10);
  try{
    const taskUpdate = await prisma.task.update({
      where: {id: taskId},
      data: {
        title: title,
        description: description
      },
    })
    res.status(201).json(taskUpdate);
  }
  catch(error){
    res.status(500).json({ error: 'Something went wrong' });
  }
});

// Example route to delete a task by ID
app.delete('/tasks/:id', async (req, res) => {
  const taskId = parseInt(req.params.id, 10);
  try{
    const deleteTask = await prisma.task.delete({ where: {
      id: taskId,
    }});
    res.status(201).json(deleteTask);
  }
  catch (error){
    res.status(500).json({ error: 'Something went wrong' });
  }
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