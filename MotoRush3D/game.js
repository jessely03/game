// --- GAME STATE ---
let scene, camera, renderer;
let ambientLight, directionalLight, blueLight, redLight;
let isPlaying = false;
let isPaused = false;
let score = 0;
let coins = 0;
let speed = 0;
let maxSpeed = 300;
let distance = 0;

let isDay = false;
let isEasy = false;

// --- GARAGE STATE ---
let savedCoins = parseInt(localStorage.getItem('motoCoins') || '0');
let ownedVehicles = JSON.parse(localStorage.getItem('motoVehicles') || '["basic-bike"]');
let currentVehicle = localStorage.getItem('motoSelected') || 'basic-bike';

// --- OBJECTS ---
let playerBike;
let playerSpeed = 0;
let playerTargetX = 0;
let playerCurrentX = 0;
const ROAD_WIDTH = 40;
const LANE_WIDTH = ROAD_WIDTH / 3;

let objects = []; // Coins and Cars
let scenery = []; // Buildings
let roadGrid;
let horizon;

// --- DOM ELEMENTS ---
const menuScreen = document.getElementById('menu-screen');
const hudScreen = document.getElementById('hud-screen');
const gameOverScreen = document.getElementById('gameover-screen');
const scoreVal = document.getElementById('score-val');
const coinVal = document.getElementById('coin-val');
const speedVal = document.getElementById('speed-val');
const finalScore = document.getElementById('final-score');
const finalCoins = document.getElementById('final-coins');

document.getElementById('start-btn').addEventListener('click', startGame);
document.getElementById('restart-btn').addEventListener('click', startGame);

// --- INIT THREE.JS ---
function init() {
    const container = document.getElementById('game-container');
    
    // Scene
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x050510, 0.004);
    
    // Camera
    camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 7, 15);
    camera.lookAt(0, 0, -30);
    
    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setClearColor(0x050510);
    container.appendChild(renderer.domElement);
    
    // Lighting
    ambientLight = new THREE.AmbientLight(0x404040); // Soft white light
    scene.add(ambientLight);
    
    directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(0, 50, 0);
    scene.add(directionalLight);

    blueLight = new THREE.PointLight(0x00f0ff, 1, 100);
    blueLight.position.set(-10, 5, 0);
    scene.add(blueLight);

    redLight = new THREE.PointLight(0xff003c, 1, 100);
    redLight.position.set(10, 5, 0);
    scene.add(redLight);
    
    createEnvironment();
    createPlayer();
    
    // Resize handler
    window.addEventListener('resize', onWindowResize, false);
    
    // Input
    document.addEventListener('keydown', onKeyDown);
    document.addEventListener('keyup', onKeyUp);
    
    animate();
}

function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

function createEnvironment() {
    // Road Ground
    const planeGeo = new THREE.PlaneGeometry(ROAD_WIDTH, 1000);
    const planeMat = new THREE.MeshStandardMaterial({ 
        color: 0x111111,
        roughness: 0.2,
        metalness: 0.8
    });
    const ground = new THREE.Mesh(planeGeo, planeMat);
    ground.rotation.x = -Math.PI / 2;
    scene.add(ground);
    
    // Neon Grid (Moving)
    const gridHelper = new THREE.GridHelper(1000, 100, 0x00f0ff, 0x002030);
    gridHelper.position.y = 0.1;
    scene.add(gridHelper);
    roadGrid = gridHelper;
    
    // Horizon glow
    const horizGeo = new THREE.PlaneGeometry(500, 100);
    const horizMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.1 });
    horizon = new THREE.Mesh(horizGeo, horizMat);
    horizon.position.set(0, 20, -300);
    scene.add(horizon);
    
    // Scenery Buildings
    for (let z = 0; z > -800; z -= 60) {
        spawnScenery(z);
    }
}

function createProceduralBuilding() {
    const building = new THREE.Group();
    
    const height = 20 + Math.random() * 80;
    const width = 10 + Math.random() * 20;
    const depth = 10 + Math.random() * 20;
    
    const geo = new THREE.BoxGeometry(width, height, depth);
    const mat = new THREE.MeshStandardMaterial({ 
        color: 0x0a0a1a, 
        roughness: 0.9, 
        metalness: 0.1 
    });
    
    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.y = height / 2;
    building.add(mesh);
    
    // Add neon edges
    if (Math.random() > 0.2) {
        const edges = new THREE.EdgesGeometry(geo);
        const colors = [0x00f0ff, 0xff003c, 0xffd700, 0x8800ff];
        const neonColor = colors[Math.floor(Math.random() * colors.length)];
        const lineMat = new THREE.LineBasicMaterial({ color: neonColor, transparent: true, opacity: 0.3 });
        const wireframe = new THREE.LineSegments(edges, lineMat);
        wireframe.position.y = height / 2;
        building.add(wireframe);
    }
    
    return building;
}

function spawnScenery(zPos) {
    // Left side building
    const leftBuilding = createProceduralBuilding();
    leftBuilding.position.set(-ROAD_WIDTH/2 - 15 - Math.random() * 40, 0, zPos);
    scene.add(leftBuilding);
    scenery.push(leftBuilding);
    
    // Right side building
    const rightBuilding = createProceduralBuilding();
    rightBuilding.position.set(ROAD_WIDTH/2 + 15 + Math.random() * 40, 0, zPos);
    scene.add(rightBuilding);
    scenery.push(rightBuilding);
}

function createProceduralMotorcycle(mainColor, neonColor) {
    const bike = new THREE.Group();
    
    const bodyMat = new THREE.MeshStandardMaterial({ color: mainColor, metalness: 0.9, roughness: 0.2 });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111, metalness: 0.8, roughness: 0.5 });
    const neonMat = new THREE.MeshBasicMaterial({ color: neonColor });
    const chromeMat = new THREE.MeshStandardMaterial({ color: 0xdddddd, metalness: 1.0, roughness: 0.1 });
    
    // Wheels (Front and Back)
    const wheelGeo = new THREE.TorusGeometry(0.7, 0.25, 16, 32);
    const wheelMat = new THREE.MeshStandardMaterial({ color: 0x050505, roughness: 0.9 });
    
    const backWheel = new THREE.Mesh(wheelGeo, wheelMat);
    backWheel.position.set(0, 0.95, 1.8);
    bike.add(backWheel);
    
    const frontWheel = new THREE.Mesh(wheelGeo, wheelMat);
    frontWheel.position.set(0, 0.95, -1.8);
    bike.add(frontWheel);
    
    // Wheel Neons
    const rimGeo = new THREE.TorusGeometry(0.5, 0.05, 16, 32);
    const backRim = new THREE.Mesh(rimGeo, neonMat);
    backWheel.add(backRim);
    const frontRim = new THREE.Mesh(rimGeo, neonMat);
    frontWheel.add(frontRim);
    
    // Chassis Frame
    const frameGeo = new THREE.BoxGeometry(0.6, 0.6, 3);
    const frame = new THREE.Mesh(frameGeo, darkMat);
    frame.position.set(0, 1.2, 0);
    bike.add(frame);
    
    // Gas Tank
    const tankGeo = new THREE.CylinderGeometry(0.6, 0.6, 1.2, 16);
    const tank = new THREE.Mesh(tankGeo, bodyMat);
    tank.rotation.z = Math.PI / 2;
    tank.position.set(0, 1.8, -0.5);
    bike.add(tank);
    
    // Seat
    const seatGeo = new THREE.BoxGeometry(0.6, 0.2, 1.2);
    const seat = new THREE.Mesh(seatGeo, new THREE.MeshStandardMaterial({color: 0x000000}));
    seat.position.set(0, 1.6, 0.8);
    bike.add(seat);
    
    // Front Forks
    const forkGeo = new THREE.CylinderGeometry(0.08, 0.08, 2.2);
    const forkL = new THREE.Mesh(forkGeo, chromeMat);
    forkL.position.set(-0.3, 1.7, -1.6);
    forkL.rotation.x = -Math.PI / 8;
    bike.add(forkL);
    
    const forkR = new THREE.Mesh(forkGeo, chromeMat);
    forkR.position.set(0.3, 1.7, -1.6);
    forkR.rotation.x = -Math.PI / 8;
    bike.add(forkR);
    
    // Handlebars
    const barGeo = new THREE.CylinderGeometry(0.05, 0.05, 1.4);
    const handlebars = new THREE.Mesh(barGeo, darkMat);
    handlebars.rotation.z = Math.PI / 2;
    handlebars.position.set(0, 2.5, -1.2);
    bike.add(handlebars);
    
    // Headlight
    const lightGeo = new THREE.SphereGeometry(0.25);
    const headlight = new THREE.Mesh(lightGeo, new THREE.MeshBasicMaterial({color: 0xffffff}));
    headlight.position.set(0, 2.0, -2.1);
    bike.add(headlight);
    
    // Headlight Glow (PointLight)
    const pLight = new THREE.PointLight(0xffffff, 1, 20);
    pLight.position.set(0, 2.0, -2.3);
    bike.add(pLight);
    
    // Exhaust
    const exhaustGeo = new THREE.CylinderGeometry(0.12, 0.12, 1.8);
    const exhaust = new THREE.Mesh(exhaustGeo, chromeMat);
    exhaust.rotation.x = Math.PI / 2;
    exhaust.position.set(0.4, 1.0, 1.2);
    bike.add(exhaust);

    // Neon Underglow
    const underGeo = new THREE.BoxGeometry(0.8, 0.1, 2.5);
    const under = new THREE.Mesh(underGeo, neonMat);
    under.position.set(0, 0.5, 0);
    bike.add(under);
    
    return bike;
}

function createPlayer() {
    if (currentVehicle === 'sport-bike') {
        playerBike = createProceduralMotorcycle(0x22cc22, 0x8800ff); // Green/Purple
        // Make it look a bit lower and faster
        playerBike.scale.set(1.0, 0.8, 1.1);
    } else if (currentVehicle === 'muscle-car') {
        playerBike = createProceduralCar(0xff0000); // Red car
        playerBike.scale.set(0.6, 0.6, 0.6); // Scale down slightly to fit lane
    } else {
        playerBike = createProceduralMotorcycle(0xff003c, 0x00f0ff); // Default Red/Cyan
    }
    
    playerBike.position.z = 0;
    scene.add(playerBike);
}

// --- SETTINGS & GARAGE LOGIC ---
function toggleEnvironment() {
    isDay = !isDay;
    const btn = document.getElementById('toggle-env-btn');
    
    if (isDay) {
        btn.innerText = "DAY MODE";
        scene.fog.color.setHex(0xaaaaaa);
        scene.fog.density = 0.002;
        renderer.setClearColor(0x87CEEB); // Sky blue
        
        ambientLight.color.setHex(0xffffff);
        ambientLight.intensity = 1.0;
        directionalLight.intensity = 1.5;
        
        horizon.material.color.setHex(0xffffff);
        horizon.material.opacity = 0.5;
        roadGrid.material.color.setHex(0x888888);
    } else {
        btn.innerText = "NIGHT MODE";
        scene.fog.color.setHex(0x050510);
        scene.fog.density = 0.004;
        renderer.setClearColor(0x050510);
        
        ambientLight.color.setHex(0x404040);
        ambientLight.intensity = 1.0;
        directionalLight.intensity = 0.8;
        
        horizon.material.color.setHex(0x00f0ff);
        horizon.material.opacity = 0.1;
        roadGrid.material.color.setHex(0x00f0ff);
    }
}

function toggleDifficulty() {
    isEasy = !isEasy;
    const btn = document.getElementById('toggle-diff-btn');
    if (isEasy) {
        btn.innerText = "EASY MODE";
    } else {
        btn.innerText = "NORMAL MODE";
    }
}

function openGarage() {
    menuScreen.classList.add('hidden');
    document.getElementById('garage-screen').classList.remove('hidden');
    updateGarageUI();
}

function closeGarage() {
    document.getElementById('garage-screen').classList.add('hidden');
    menuScreen.classList.remove('hidden');
    
    // Recreate player visually to show selected vehicle
    scene.remove(playerBike);
    createPlayer();
}

function syncCoins(amount) {
    savedCoins += amount;
    localStorage.setItem('motoCoins', savedCoins);
}

function updateGarageUI() {
    document.getElementById('garage-coins').innerText = savedCoins;
    
    const vehicles = [
        { id: 'basic-bike', cost: 0 },
        { id: 'sport-bike', cost: 500 },
        { id: 'muscle-car', cost: 1000 }
    ];
    
    vehicles.forEach(v => {
        const btn = document.getElementById(`btn-${v.id}`);
        if (currentVehicle === v.id) {
            btn.innerText = "EQUIPPED";
            btn.style.borderColor = "var(--gold)";
            btn.style.color = "var(--gold)";
        } else if (ownedVehicles.includes(v.id)) {
            btn.innerText = "SELECT";
            btn.style.borderColor = "var(--primary)";
            btn.style.color = "var(--primary)";
        } else {
            btn.innerText = "BUY";
            btn.style.borderColor = "var(--primary)";
            btn.style.color = "var(--primary)";
        }
    });
}

function buyOrSelectVehicle(id, cost) {
    if (ownedVehicles.includes(id)) {
        // Equip
        currentVehicle = id;
        localStorage.setItem('motoSelected', currentVehicle);
    } else {
        // Buy
        if (savedCoins >= cost) {
            syncCoins(-cost);
            ownedVehicles.push(id);
            localStorage.setItem('motoVehicles', JSON.stringify(ownedVehicles));
            currentVehicle = id;
            localStorage.setItem('motoSelected', currentVehicle);
        } else {
            alert("Not enough coins!");
        }
    }
    updateGarageUI();
}

// --- INPUT ---
const keys = { w: false, a: false, s: false, d: false, ArrowLeft: false, ArrowRight: false, ArrowUp: false, ArrowDown: false };

function onKeyDown(e) {
    let k = e.key;
    if (k.length === 1) k = k.toLowerCase();
    if (keys.hasOwnProperty(k)) keys[k] = true;
}

function onKeyUp(e) {
    let k = e.key;
    if (k.length === 1) k = k.toLowerCase();
    if (keys.hasOwnProperty(k)) keys[k] = false;
}

// --- GAME LOGIC ---
function startGame() {
    menuScreen.classList.add('hidden');
    gameOverScreen.classList.add('hidden');
    hudScreen.classList.remove('hidden');
    
    isPlaying = true;
    isPaused = false;
    score = 0;
    coins = 0;
    speed = 0;
    distance = 0;
    playerCurrentX = 0;
    playerTargetX = 0;
    playerBike.position.x = 0;
    playerBike.rotation.z = 0;
    
    maxSpeed = isEasy ? 200 : 300;
    
    updateHUD();
    
    // Clear old objects
    objects.forEach(obj => scene.remove(obj.mesh));
    objects = [];
}

function gameOver() {
    isPlaying = false;
    isPaused = false;
    hudScreen.classList.add('hidden');
    gameOverScreen.classList.remove('hidden');
    
    syncCoins(coins);
    finalScore.innerText = Math.floor(score);
    finalCoins.innerText = coins;
}

function spawnObject() {
    if (Math.random() > 0.5) {
        spawnCar();
    } else {
        spawnCoin();
    }
}

function createProceduralCar(color) {
    const car = new THREE.Group();
    const bodyMat = new THREE.MeshStandardMaterial({ color: color, metalness: 0.7, roughness: 0.3 });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.8 });
    const glassMat = new THREE.MeshStandardMaterial({ color: 0x222222, metalness: 0.9, roughness: 0.1 });
    
    // Lower body
    const bodyGeo = new THREE.BoxGeometry(2.5, 1.2, 5);
    const body = new THREE.Mesh(bodyGeo, bodyMat);
    body.position.y = 0.6;
    car.add(body);
    
    // Cabin (top part)
    const cabinGeo = new THREE.BoxGeometry(2.0, 1.0, 2.5);
    const cabin = new THREE.Mesh(cabinGeo, glassMat);
    cabin.position.set(0, 1.6, -0.5);
    car.add(cabin);
    
    // Wheels
    const wheelGeo = new THREE.CylinderGeometry(0.5, 0.5, 0.4, 16);
    const wheelPos = [
        [-1.3, 0.5, 1.5], [1.3, 0.5, 1.5],
        [-1.3, 0.5, -1.5], [1.3, 0.5, -1.5]
    ];
    wheelPos.forEach(pos => {
        const wheel = new THREE.Mesh(wheelGeo, darkMat);
        wheel.rotation.z = Math.PI / 2;
        wheel.position.set(pos[0], pos[1], pos[2]);
        car.add(wheel);
    });
    
    // Tail lights
    const tailLightGeo = new THREE.BoxGeometry(0.6, 0.2, 0.1);
    const tailLightMat = new THREE.MeshBasicMaterial({ color: 0xff0000 });
    const tailLightL = new THREE.Mesh(tailLightGeo, tailLightMat);
    tailLightL.position.set(-0.8, 0.8, 2.55);
    car.add(tailLightL);
    
    const tailLightR = new THREE.Mesh(tailLightGeo, tailLightMat);
    tailLightR.position.set(0.8, 0.8, 2.55);
    car.add(tailLightR);
    
    return car;
}

function createProceduralTruck(color) {
    const truck = new THREE.Group();
    const cabMat = new THREE.MeshStandardMaterial({ color: color, metalness: 0.6, roughness: 0.4 });
    const trailerMat = new THREE.MeshStandardMaterial({ color: 0xdddddd, metalness: 0.2, roughness: 0.8 });
    const darkMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.8 });
    
    // Cabin
    const cabGeo = new THREE.BoxGeometry(3, 3, 2.5);
    const cab = new THREE.Mesh(cabGeo, cabMat);
    cab.position.set(0, 1.8, -3.5);
    truck.add(cab);
    
    // Trailer
    const trailerGeo = new THREE.BoxGeometry(3.2, 4, 7);
    const trailer = new THREE.Mesh(trailerGeo, trailerMat);
    trailer.position.set(0, 2.5, 1.5);
    truck.add(trailer);
    
    // Wheels (6 wheels)
    const wheelGeo = new THREE.CylinderGeometry(0.6, 0.6, 0.6, 16);
    const wheelPos = [
        [-1.7, 0.6, -3.5], [1.7, 0.6, -3.5], // Cab front
        [-1.7, 0.6, 0], [1.7, 0.6, 0],       // Trailer middle
        [-1.7, 0.6, 4], [1.7, 0.6, 4]        // Trailer back
    ];
    wheelPos.forEach(pos => {
        const wheel = new THREE.Mesh(wheelGeo, darkMat);
        wheel.rotation.z = Math.PI / 2;
        wheel.position.set(pos[0], pos[1], pos[2]);
        truck.add(wheel);
    });
    
    // Tail lights
    const tailLightGeo = new THREE.BoxGeometry(0.8, 0.3, 0.1);
    const tailLightMat = new THREE.MeshBasicMaterial({ color: 0xff0000 });
    const tailLightL = new THREE.Mesh(tailLightGeo, tailLightMat);
    tailLightL.position.set(-1.0, 1.0, 5.05);
    truck.add(tailLightL);
    
    const tailLightR = new THREE.Mesh(tailLightGeo, tailLightMat);
    tailLightR.position.set(1.0, 1.0, 5.05);
    truck.add(tailLightR);
    
    return truck;
}

function spawnCar() {
    const laneIndex = Math.floor(Math.random() * 3) - 1; // -1, 0, 1
    const xPos = laneIndex * LANE_WIDTH;
    
    const isTruck = Math.random() > 0.7;
    
    const colors = [0xff003c, 0x00f0ff, 0xffd700, 0x8800ff, 0xff8800];
    const color = colors[Math.floor(Math.random() * colors.length)];
    
    let mesh;
    let collisionW;
    
    if (isTruck) {
        mesh = createProceduralTruck(color);
        collisionW = 3.2;
    } else {
        mesh = createProceduralCar(color);
        collisionW = 2.5;
    }
    
    mesh.position.set(xPos, 0, -300);
    
    scene.add(mesh);
    objects.push({ 
        type: 'car', 
        mesh: mesh, 
        speed: isTruck ? 80 : 120,
        width: collisionW
    });
}

function spawnCoin() {
    const laneIndex = Math.floor(Math.random() * 3) - 1; // -1, 0, 1
    const xPos = laneIndex * LANE_WIDTH;
    
    // GIANT 3D COIN
    const geo = new THREE.TorusGeometry(1.5, 0.4, 16, 32);
    const mat = new THREE.MeshStandardMaterial({ 
        color: 0xffd700, 
        metalness: 1, 
        roughness: 0.1,
        emissive: 0xaa8800,
        emissiveIntensity: 0.5
    });
    const mesh = new THREE.Mesh(geo, mat);
    
    mesh.position.set(xPos, 2, -300);
    
    scene.add(mesh);
    objects.push({ type: 'coin', mesh: mesh, collected: false, floatOffset: Math.random() * Math.PI * 2 });
}

function updateHUD() {
    scoreVal.innerText = Math.floor(score);
    coinVal.innerText = coins;
    speedVal.innerText = Math.floor(speed);
}

// --- MAIN LOOP ---
const clock = new THREE.Clock();

function animate() {
    requestAnimationFrame(animate);
    
    if (isPaused) return;

    const dt = clock.getDelta();
    const time = clock.getElapsedTime();
    
    if (isPlaying) {
        // Input logic
        if (keys.w || keys.ArrowUp) {
            speed = THREE.MathUtils.lerp(speed, maxSpeed, dt * 0.5);
        } else if (keys.s || keys.ArrowDown) {
            speed = THREE.MathUtils.lerp(speed, 0, dt * 2);
        } else {
            speed = THREE.MathUtils.lerp(speed, 50, dt * 0.5); // Natural slow down
        }
        
        if (keys.a || keys.ArrowLeft) {
            playerTargetX = THREE.MathUtils.clamp(playerTargetX - LANE_WIDTH * dt * 5, -ROAD_WIDTH/2 + 2, ROAD_WIDTH/2 - 2);
        }
        if (keys.d || keys.ArrowRight) {
            playerTargetX = THREE.MathUtils.clamp(playerTargetX + LANE_WIDTH * dt * 5, -ROAD_WIDTH/2 + 2, ROAD_WIDTH/2 - 2);
        }
        
        // Move and lean bike
        const xDiff = playerTargetX - playerCurrentX;
        playerCurrentX += xDiff * dt * 5;
        playerBike.position.x = playerCurrentX;
        
        // Lean physics (only for bikes)
        if (currentVehicle !== 'muscle-car') {
            playerBike.rotation.z = -xDiff * 0.1;
        } else {
            playerBike.rotation.z = -xDiff * 0.02; // Very slight lean for car
            playerBike.rotation.y = -xDiff * 0.05; // Steer wheels visually
        }
        
        // Suspension bobbing based on speed
        playerBike.position.y = Math.sin(time * 20) * (speed / maxSpeed) * 0.1;
        
        // Camera follow
        camera.position.x = THREE.MathUtils.lerp(camera.position.x, playerCurrentX * 0.5, dt * 2);
        
        // Move Grid to simulate speed
        distance += speed * dt;
        score += speed * dt * 0.1;
        roadGrid.position.z = (distance % 10);
        
        // Move Scenery
        for (let i = 0; i < scenery.length; i++) {
            const b = scenery[i];
            b.position.z += speed * dt * 0.3;
            if (b.position.z > 30) {
                b.position.z -= 800;
            }
        }
        
        // Spawn Objects (fewer on easy mode)
        const spawnChance = isEasy ? 0.01 : 0.02;
        if (Math.random() < spawnChance + (speed / 10000)) {
            spawnObject();
        }
        
        // Update Objects
        for (let i = objects.length - 1; i >= 0; i--) {
            const obj = objects[i];
            
            if (obj.type === 'car') {
                // Cars move away relative to player speed
                obj.mesh.position.z += (speed - obj.speed) * dt * 0.3;
            } else if (obj.type === 'coin') {
                obj.mesh.position.z += speed * dt * 0.3;
                obj.mesh.rotation.y += dt * 5; // Spin fast
                obj.mesh.position.y = 2 + Math.sin(time * 5 + obj.floatOffset) * 0.5; // Hover
            }
            
            // Collision Detection
            if (obj.mesh.position.z > -4 && obj.mesh.position.z < 4) {
                const dx = Math.abs(obj.mesh.position.x - playerCurrentX);
                
                if (obj.type === 'car') {
                    const hitThreshold = (obj.width / 2) + 0.6; // 0.6 is approx half bike width
                    if (dx < hitThreshold) { // Hit!
                        gameOver();
                    }
                } else if (obj.type === 'coin' && !obj.collected) {
                    if (dx < 3) { // Collect!
                        obj.collected = true;
                        coins += 10;
                        score += 50;
                        scene.remove(obj.mesh);
                        objects.splice(i, 1);
                        continue;
                    }
                }
            }
            
            // Remove passed objects
            if (obj.mesh.position.z > 10) {
                scene.remove(obj.mesh);
                objects.splice(i, 1);
            }
        }
        
        if (Math.floor(time * 10) % 2 === 0) updateHUD();
    }
    
    renderer.render(scene, camera);
}

function togglePause() {
    if (!isPlaying) return;
    isPaused = !isPaused;
    
    const pauseScreen = document.getElementById('pause-screen');
    if (isPaused) {
        pauseScreen.classList.remove('hidden');
        clock.stop();
    } else {
        pauseScreen.classList.add('hidden');
        clock.start();
    }
}

function returnToMenu() {
    isPlaying = false;
    isPaused = false;
    
    document.getElementById('pause-screen').classList.add('hidden');
    hudScreen.classList.add('hidden');
    gameOverScreen.classList.add('hidden');
    menuScreen.classList.remove('hidden');
    
    // Save coins when returning to menu
    syncCoins(coins);
}

init();
