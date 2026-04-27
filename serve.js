const express = require('express');
const app = express();
const http = require('http').createServer(app);
const io = require('socket.io')(http);

app.use(express.static('public'));

const players = {};
const bullets = [];

io.on('connection', (socket) => {
  console.log('Conectou:', socket.id);

  socket.on('joinGame', (data) => {
    players[socket.id] = {
      id: socket.id,
      x: 1000 + Math.random() * 200,
      y: 1000 + Math.random() * 200,
      r: 20,
      name: data.name || 'Player',
      hp: 100,
      maxHp: 100,
      color: data.color || '#2196F3',
      weapon: null
    };

    socket.emit('currentPlayers', players);
    socket.broadcast.emit('newPlayer', players[socket.id]);
  });

  socket.on('playerMovement', (data) => {
    if (players[socket.id]) {
      players[socket.id].x = data.x;
      players[socket.id].y = data.y;
      socket.broadcast.emit('playerMoved', players[socket.id]);
    }
  });

  socket.on('playerShoot', (bulletData) => {
    const bullet = {
      id: Date.now() + Math.random(),
    ...bulletData,
      ownerId: socket.id
    };
    bullets.push(bullet);
    io.emit('newBullet', bullet);

    setTimeout(() => {
      const index = bullets.findIndex(b => b.id === bullet.id);
      if (index!== -1) bullets.splice(index, 1);
    }, 3000);
  });

  socket.on('pickupWeapon', (weaponData) => {
    if (players[socket.id]) {
      players[socket.id].weapon = weaponData;
      io.emit('playerUpdateWeapon', { id: socket.id, weapon: weaponData });
    }
  });

  socket.on('dropWeapon', () => {
    if (players[socket.id]) {
      players[socket.id].weapon = null;
      io.emit('playerUpdateWeapon', { id: socket.id, weapon: null });
    }
  });

  socket.on('takeDamage', (data) => {
    if (players[data.targetId]) {
      players[data.targetId].hp -= data.dmg;
      if (players[data.targetId].hp <= 0) {
        players[data.targetId].hp = 100;
        players[data.targetId].x = 1000 + Math.random() * 200;
        players[data.targetId].y = 1000 + Math.random() * 200;
        io.emit('playerDied', { id: data.targetId });
      }
      io.emit('playerHealthUpdate', { id: data.targetId, hp: players[data.targetId].hp });
    }
  });

  socket.on('disconnect', () => {
    console.log('Desconectou:', socket.id);
    delete players[socket.id];
    io.emit('playerDisconnect', socket.id);
  });
});

const PORT = process.env.PORT || 3000;
http.listen(PORT, () => console.log(`Servidor rodando na porta ${PORT}`));