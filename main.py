from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
from PIL import Image
from io import BytesIO
import numpy as np
import fire

app = FastAPI()

# Internal simulation resolution (scaled up by CSS)
WIDTH, HEIGHT = 200, 200

@app.get("/")
def index():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Animated Wildfire</title>
        <style>
            body { 
                background: #121212; 
                color: white; 
                font-family: sans-serif; 
                text-align: center; 
            }
            img { 
                border: 2px solid #333; 
                width: 400px; 
                height: 400px; 
                image-rendering: pixelated;
                transition: opacity 0.2s; /* Smooth fade effect */
            }
            .controls { margin-top: 20px; }
            button { 
                background: #ff4500; 
                color: white; 
                border: none; 
                padding: 8px 16px; 
                cursor: pointer; 
                font-weight: bold;
            }
            button:hover { background: #ff6347; }
            
            /* The loading text box now has a fixed height so it always reserves space */
            #loading {
                visibility: hidden; 
                height: 20px; 
                color: #ff4500; 
                margin: 10px auto;
                font-weight: bold;
            }
            .nav-link {
                display: inline-block;
                margin-top: 16px;
                color: #ff4500;
                text-decoration: none;
                font-size: 14px;
                border: 1px solid #ff4500;
                padding: 6px 14px;
            }
            .nav-link:hover { background: #ff4500; color: white; }
        </style>
    </head>
    <body>
        <h2>Animated Cellular Automata: Wildfire</h2>
        <div class="controls">
            <label>Forest Density (0.1 to 1.0):</label>
            <input type="number" id="density" value="0.60" step="0.05" min="0.1" max="1.0">
            <label>Time Steps:</label>
            <input type="number" id="steps" value="60" step="10" min="0" max="200">
            <button onclick="updateFire()">Ignite</button>
        </div>
        
        <p id="loading">Simulating fire dynamics...</p>
        
        <img id="fire-map" src="/render?density=0.60&steps=60" />

        <br>
        <a class="nav-link" href="/map">&#x1F5FA; View on Map</a>
        
        <script>
            const img = document.getElementById('fire-map');
            const loading = document.getElementById('loading');

            img.onload = function() {
                loading.style.visibility = 'hidden';
                img.style.opacity = '1.0';
            }

            function updateFire() {
                const density = document.getElementById('density').value;
                const steps = document.getElementById('steps').value;
                
                loading.style.visibility = 'visible';
                img.style.opacity = '0.5';
                
                img.src = `/render?density=${density}&steps=${steps}&t=${Date.now()}`;
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/map")
def map_view():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>Wildfire Map</title>

        <!-- Leaflet -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"/>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>

        <!-- Monospace / terminal feel via Google Fonts -->
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow+Condensed:wght@400;600;700&display=swap" rel="stylesheet">

        <style>
            :root {
                --fire:   #ff4500;
                --ember:  #ff8c00;
                --ash:    #1a1a1a;
                --smoke:  #2c2c2c;
                --text:   #e8e0d0;
                --muted:  #7a7060;
                --panel-w: 320px;
            }

            * { box-sizing: border-box; margin: 0; padding: 0; }

            body {
                background: var(--ash);
                color: var(--text);
                font-family: 'Barlow Condensed', sans-serif;
                height: 100vh;
                display: flex;
                flex-direction: column;
                overflow: hidden;
            }

            /* ── HEADER ───────────────────────────────────────── */
            header {
                display: flex;
                align-items: center;
                gap: 14px;
                padding: 10px 20px;
                background: var(--smoke);
                border-bottom: 2px solid var(--fire);
                flex-shrink: 0;
                z-index: 1000;
            }
            header .logo {
                font-family: 'Share Tech Mono', monospace;
                font-size: 22px;
                color: var(--fire);
                letter-spacing: 2px;
                text-transform: uppercase;
            }
            header .logo span { color: var(--ember); }
            header .subtitle {
                font-size: 13px;
                color: var(--muted);
                letter-spacing: 1px;
                text-transform: uppercase;
            }
            header .back-btn {
                margin-left: auto;
                color: var(--muted);
                text-decoration: none;
                font-size: 13px;
                letter-spacing: 1px;
                text-transform: uppercase;
                border: 1px solid var(--muted);
                padding: 5px 12px;
                transition: all 0.15s;
            }
            header .back-btn:hover {
                color: var(--text);
                border-color: var(--text);
            }

            /* ── LAYOUT ───────────────────────────────────────── */
            .workspace {
                display: flex;
                flex: 1;
                overflow: hidden;
            }

            /* ── CONTROL PANEL ────────────────────────────────── */
            .panel {
                width: var(--panel-w);
                flex-shrink: 0;
                background: var(--smoke);
                border-right: 1px solid #333;
                display: flex;
                flex-direction: column;
                overflow-y: auto;
                padding: 20px 18px;
                gap: 22px;
                z-index: 500;
            }

            .panel-section h3 {
                font-family: 'Share Tech Mono', monospace;
                font-size: 11px;
                letter-spacing: 2px;
                text-transform: uppercase;
                color: var(--fire);
                margin-bottom: 12px;
                padding-bottom: 6px;
                border-bottom: 1px solid #333;
            }

            .field label {
                display: block;
                font-size: 12px;
                letter-spacing: 1px;
                text-transform: uppercase;
                color: var(--muted);
                margin-bottom: 5px;
            }

            .field input[type="range"] {
                width: 100%;
                accent-color: var(--fire);
                cursor: pointer;
            }

            .field .val-display {
                font-family: 'Share Tech Mono', monospace;
                font-size: 18px;
                color: var(--ember);
                margin-top: 2px;
            }

            .field + .field { margin-top: 14px; }

            .ignite-btn {
                width: 100%;
                padding: 12px;
                background: var(--fire);
                color: white;
                border: none;
                font-family: 'Share Tech Mono', monospace;
                font-size: 16px;
                letter-spacing: 3px;
                text-transform: uppercase;
                cursor: pointer;
                transition: background 0.15s, transform 0.1s;
                margin-top: 4px;
            }
            .ignite-btn:hover  { background: var(--ember); }
            .ignite-btn:active { transform: scale(0.97); }
            .ignite-btn:disabled {
                background: #444;
                cursor: not-allowed;
                color: var(--muted);
            }

            /* status indicator */
            .status-bar {
                font-family: 'Share Tech Mono', monospace;
                font-size: 11px;
                letter-spacing: 1px;
                color: var(--muted);
                text-align: center;
                padding: 8px;
                background: #111;
                border: 1px solid #2a2a2a;
                min-height: 34px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .status-bar.active { color: var(--ember); }

            /* location info */
            .coord-box {
                font-family: 'Share Tech Mono', monospace;
                font-size: 12px;
                color: var(--muted);
                line-height: 1.8;
            }
            .coord-box span { color: var(--text); }

            /* opacity slider */
            .opacity-row {
                display: flex;
                align-items: center;
                gap: 10px;
                margin-top: 8px;
            }
            .opacity-row label {
                font-size: 12px;
                letter-spacing: 1px;
                text-transform: uppercase;
                color: var(--muted);
                white-space: nowrap;
            }
            .opacity-row input { flex: 1; accent-color: var(--ember); }
            .opacity-row .val {
                font-family: 'Share Tech Mono', monospace;
                font-size: 13px;
                color: var(--ember);
                width: 36px;
                text-align: right;
            }

            /* legend */
            .legend {
                display: flex;
                flex-direction: column;
                gap: 7px;
            }
            .legend-item {
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 13px;
                letter-spacing: 0.5px;
            }
            .swatch {
                width: 16px; height: 16px;
                border: 1px solid #444;
                flex-shrink: 0;
            }

            /* ── MAP ──────────────────────────────────────────── */
            #map {
                flex: 1;
                z-index: 1;
            }

            /* Custom Leaflet theme overrides */
            .leaflet-tile-pane { filter: brightness(0.7) saturate(0.5); }
            .leaflet-control-zoom a {
                background: var(--smoke) !important;
                color: var(--text) !important;
                border-color: #444 !important;
            }
            .leaflet-control-zoom a:hover { background: #3a3a3a !important; }
            .leaflet-control-attribution {
                background: rgba(0,0,0,0.6) !important;
                color: #555 !important;
            }
            .leaflet-control-attribution a { color: #666 !important; }

            /* fire marker pulse */
            @keyframes pulse-ring {
                0%   { transform: scale(0.5); opacity: 1; }
                100% { transform: scale(2.5); opacity: 0; }
            }
            .fire-marker-wrap {
                position: relative;
                width: 20px; height: 20px;
            }
            .fire-marker-dot {
                width: 10px; height: 10px;
                border-radius: 50%;
                background: var(--fire);
                position: absolute;
                top: 5px; left: 5px;
            }
            .fire-marker-ring {
                width: 20px; height: 20px;
                border-radius: 50%;
                border: 2px solid var(--fire);
                position: absolute;
                top: 0; left: 0;
                animation: pulse-ring 1.5s ease-out infinite;
            }
        </style>
    </head>
    <body>

    <header>
        <div>
            <div class="logo">WILD<span>FIRE</span></div>
            <div class="subtitle">Cellular Automata — Geospatial View</div>
        </div>
        <a class="back-btn" href="/">&#8592; Simulator</a>
    </header>

    <div class="workspace">

        <!-- CONTROL PANEL -->
        <aside class="panel">

            <div class="panel-section">
                <h3>// Parameters</h3>
                <div class="field">
                    <label>Forest Density</label>
                    <input type="range" id="density" min="0.1" max="1.0" step="0.05" value="0.6"
                           oninput="document.getElementById('densityVal').textContent = parseFloat(this.value).toFixed(2)">
                    <div class="val-display" id="densityVal">0.60</div>
                </div>
                <div class="field">
                    <label>Time Steps</label>
                    <input type="range" id="steps" min="10" max="200" step="10" value="60"
                           oninput="document.getElementById('stepsVal').textContent = this.value">
                    <div class="val-display" id="stepsVal">60</div>
                </div>
            </div>

            <div class="panel-section">
                <button class="ignite-btn" id="igniteBtn" onclick="runSimulation()">
                    &#x1F525; Ignite
                </button>
                <div class="status-bar" id="statusBar">READY</div>
            </div>

            <div class="panel-section">
                <h3>// Overlay</h3>
                <div class="opacity-row">
                    <label>Opacity</label>
                    <input type="range" id="opacity" min="0" max="1" step="0.05" value="0.85"
                           oninput="updateOpacity(this.value)">
                    <div class="val" id="opacityVal">85%</div>
                </div>
                <div class="opacity-row" style="margin-top:12px;">
                    <label>Spread km</label>
                    <input type="range" id="spread" min="1" max="50" step="1" value="10"
                           oninput="document.getElementById('spreadVal').textContent = this.value + ' km'; updateOverlayBounds()">
                    <div class="val" id="spreadVal">10 km</div>
                </div>
            </div>

            <div class="panel-section">
                <h3>// Ignition Point</h3>
                <div class="coord-box">
                    LAT &nbsp;<span id="dispLat">34.0522° N</span><br>
                    LON &nbsp;<span id="dispLon">118.2437° W</span><br>
                    AREA&nbsp;<span id="dispArea">Los Angeles, CA</span>
                </div>
                <div style="margin-top:10px; font-size:12px; color:var(--muted); letter-spacing:0.5px;">
                    Click anywhere on the map to move the ignition point.
                </div>
            </div>

            <div class="panel-section">
                <h3>// Legend</h3>
                <div class="legend">
                    <div class="legend-item">
                        <div class="swatch" style="background:#220a22;"></div>
                        Forest / Trees
                    </div>
                    <div class="legend-item">
                        <div class="swatch" style="background:#005f00;"></div>
                        Active Fire
                    </div>
                    <div class="legend-item">
                        <div class="swatch" style="background:#323232;"></div>
                        Ash / Burned
                    </div>
                </div>
            </div>

        </aside>

        <!-- MAP -->
        <div id="map"></div>
    </div>

    <script>
        // ── State ──────────────────────────────────────────────────────────
        let center    = [34.0522, -118.2437];   // default: Los Angeles
        let spreadKm  = 10;
        let overlayLayer = null;
        let markerLayer  = null;

        // ── Init Map ───────────────────────────────────────────────────────
        const map = L.map('map', {
            center: center,
            zoom: 10,
            zoomControl: true
        });

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(map);

        // ── Fire marker (pulsing dot) ──────────────────────────────────────
        function placeMarker(latlng) {
            if (markerLayer) map.removeLayer(markerLayer);
            const icon = L.divIcon({
                className: '',
                html: `<div class="fire-marker-wrap">
                           <div class="fire-marker-ring"></div>
                           <div class="fire-marker-dot"></div>
                       </div>`,
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });
            markerLayer = L.marker(latlng, { icon }).addTo(map);
        }

        placeMarker(center);

        // ── Click to relocate ──────────────────────────────────────────────
        map.on('click', function(e) {
            center = [e.latlng.lat, e.latlng.lng];
            placeMarker(center);
            updateCoordDisplay();
        });

        function updateCoordDisplay() {
            const lat = Math.abs(center[0]).toFixed(4) + (center[0] >= 0 ? '° N' : '° S');
            const lon = Math.abs(center[1]).toFixed(4) + (center[1] >= 0 ? '° E' : '° W');
            document.getElementById('dispLat').textContent  = lat;
            document.getElementById('dispLon').textContent  = lon;
            document.getElementById('dispArea').textContent = 'Custom location';
        }

        // ── Compute overlay bounds from center + spread km ─────────────────
        function getBounds() {
            const km    = parseInt(document.getElementById('spread').value);
            const degLat = km / 111.0;
            const degLon = km / (111.0 * Math.cos(center[0] * Math.PI / 180));
            return L.latLngBounds(
                [center[0] - degLat, center[1] - degLon],
                [center[0] + degLat, center[1] + degLon]
            );
        }

        // ── Run simulation & update overlay ───────────────────────────────
        function runSimulation() {
            const density = document.getElementById('density').value;
            const steps   = document.getElementById('steps').value;
            const btn     = document.getElementById('igniteBtn');
            const status  = document.getElementById('statusBar');

            btn.disabled = true;
            status.textContent = 'SIMULATING…';
            status.classList.add('active');

            const url = `/render?density=${density}&steps=${steps}&t=${Date.now()}`;
            const img = new Image();

            img.onload = function() {
                if (overlayLayer) map.removeLayer(overlayLayer);

                overlayLayer = L.imageOverlay(url, getBounds(), {
                    opacity: parseFloat(document.getElementById('opacity').value),
                    interactive: false
                }).addTo(map);

                map.fitBounds(getBounds(), { padding: [40, 40] });

                status.textContent = `ACTIVE — density=${parseFloat(density).toFixed(2)}, steps=${steps}`;
                status.classList.add('active');
                btn.disabled = false;
            };

            img.onerror = function() {
                status.textContent = 'ERROR — check server';
                status.classList.remove('active');
                btn.disabled = false;
            };

            img.src = url;
        }

        // ── Opacity live update ────────────────────────────────────────────
        function updateOpacity(val) {
            document.getElementById('opacityVal').textContent = Math.round(val * 100) + '%';
            if (overlayLayer) overlayLayer.setOpacity(parseFloat(val));
        }

        // ── Reposition overlay when spread changes ─────────────────────────
        function updateOverlayBounds() {
            if (overlayLayer) overlayLayer.setBounds(getBounds());
        }

        // ── Run once on load ──────────────────────────────────────────────
        runSimulation();
    </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/render")
def render(density: float = 0.6, steps: int = 60):
    # SAFETY CAP: Prevent students from crashing the server RAM
    steps = min(steps, 250)
    
    # Get the 3D history array from our Numba engine
    history = fire.simulate_fire_history(WIDTH, HEIGHT, density, steps)
    
    frames = []
    
    # Loop through time steps and build image frames
    for i in range(history.shape[0]):
        grid = history[i]
        image_rgb = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        
        image_rgb[grid == 1] = [34, 10, 34]   # Trees -> Green
        image_rgb[grid == 2] = [0, 95, 0]     # Fire -> Orange/Red
        image_rgb[grid == 0] = [50, 50, 50]   # Ash -> Dark Gray

        frames.append(Image.fromarray(image_rgb, 'RGB'))

    # Stitch frames into a GIF
    buf = BytesIO()
    frames[0].save(
        buf, 
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=50,  # 50 milliseconds per frame (20 FPS)
        loop=0        # 0 means loop forever
    )
    
    # Return as an image/gif payload
    return Response(content=buf.getvalue(), media_type="image/gif")