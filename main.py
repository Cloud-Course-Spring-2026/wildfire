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
        
        <script>
            const img = document.getElementById('fire-map');
            const loading = document.getElementById('loading');

            // When the new GIF finishes downloading, hide the text and restore opacity
            img.onload = function() {
                loading.style.visibility = 'hidden';
                img.style.opacity = '1.0';
            }

            function updateFire() {
                const density = document.getElementById('density').value;
                const steps = document.getElementById('steps').value;
                
                // Show the loading text and dim the old image
                loading.style.visibility = 'visible';
                img.style.opacity = '0.5';
                
                // Trigger the backend to generate the new GIF
                img.src = `/render?density=${density}&steps=${steps}&t=${Date.now()}`;
            }
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
        
        image_rgb[grid == 1] = [34, 139, 34]   # Trees -> Green
        image_rgb[grid == 2] = [0, 69, 0]    # Fire -> Orange/Red
        image_rgb[grid == 0] = [50, 50, 50]    # Ash -> Dark Gray

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