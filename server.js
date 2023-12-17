const express = require('express');
const https = require('https');
const fs = require('fs');
const bodyParser = require('body-parser');
const path = require('path');
const app = express();
app.use(bodyParser.json());

// Function to get the next file ID
function getNextFileId() {
    const files = fs.readdirSync('./data').filter(file => path.extname(file) === '.json');
    const ids = files.map(file => parseInt(file.split('.')[0], 10)).sort((a, b) => a - b);
    const highestId = ids.length > 0 ? ids[ids.length - 1] : 0;
    return highestId + 1;
}

// Function to write a JSON file
function writeJsonFile(data) {
    const newId = getNextFileId();
    fs.writeFileSync(`./data/${newId}.json`, JSON.stringify(data, null, 2), 'utf8');
    return newId;
}

const options = {
  key: fs.readFileSync('server.key'),
  cert: fs.readFileSync('server.cert')
};

// Function to read a JSON file
function readJsonFile(id) {
  try {
    return JSON.parse(fs.readFileSync(`./data/${id}.json`, 'utf8'));
  } catch (error) {
    return null;
  }
}


app.get('/', (req, res) => {
  res.send('Welcome to the User Management Service');
});

// GET request to retrieve a user
app.get('/users/:id', (req, res) => {
  const userData = readJsonFile(req.params.id);
  if (userData) {
    res.json(userData);
  } else {
    res.status(404).send('User not found');
  }
});

// POST request to create a new user
app.post('/users', (req, res) => {
    const newId = writeJsonFile(req.body);
    res.status(201).send(`User created with ID: ${newId}`);
});

https.createServer(options, app).listen(443, '192.168.7.160', () => {
  console.log('HTTPS server running on https://192.168.7.160:443');
});


app.get('/user-info/:userId', (req, res) => {
  res.sendFile(path.join(__dirname, 'user.html'));
});

app.get('/users/:id', (req, res) => {
  const userId = req.params.id;
  const filePath = path.join(__dirname, 'data', `${userId}.json`);
  if (fs.existsSync(filePath)) {
    res.sendFile(filePath);
  } else {
    res.status(404).send('User not found');
  }
});

app.get('/mapa.json', (req, res) => {
  res.sendFile(path.join(__dirname, 'mapa.json'));
});

app.get('/mapa', (req, res) => {
  res.sendFile(path.join(__dirname, 'map.html'));
});

