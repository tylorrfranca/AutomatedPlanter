#!/usr/bin/env python3
"""
Web Interface for Automated Planter
Provides monitoring and control interface for Raspberry Pi
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for
import json
import os
from datetime import datetime, timedelta
from plant_config import PlantConfig
from plant_database import PlantDatabase

app = Flask(__name__)
app.secret_key = 'automated_planter_secret_key'

# Initialize components
plant_config = PlantConfig()
plant_db = PlantDatabase()

@app.route('/')
def index():
    """Main dashboard page"""
    active_plants = plant_config.config["active_plants"]
    available_plants = plant_config.list_available_plants()
    
    # Get system status
    system_status = {
        "total_plants": len(active_plants),
        "plants_needing_water": len(plant_config.get_plants_needing_water()),
        "sensors_enabled": sum(1 for sensor in plant_config.config["sensors"].values() if sensor["enabled"]),
        "actuators_enabled": sum(1 for actuator in plant_config.config["actuators"].values() if actuator["enabled"])
    }
    
    return render_template('dashboard.html', 
                         active_plants=active_plants,
                         available_plants=available_plants,
                         system_status=system_status)

@app.route('/api/plants')
def api_get_plants():
    """Get all active plants"""
    return jsonify(plant_config.config["active_plants"])

@app.route('/api/plants/available')
def api_get_available_plants():
    """Get all available plants from database"""
    return jsonify(plant_config.list_available_plants())

@app.route('/api/plants/add', methods=['POST'])
def api_add_plant():
    """Add a new plant to the system"""
    data = request.get_json()
    plant_name = data.get('name')
    position = data.get('position', 0)
    
    if not plant_name:
        return jsonify({"error": "Plant name is required"}), 400
    
    success = plant_config.add_plant(plant_name, position)
    if success:
        return jsonify({"message": f"Added {plant_name} at position {position}"})
    else:
        return jsonify({"error": f"Failed to add {plant_name}"}), 400

@app.route('/api/plants/remove/<int:position>', methods=['DELETE'])
def api_remove_plant(position):
    """Remove a plant from the system"""
    success = plant_config.remove_plant(position)
    if success:
        return jsonify({"message": f"Removed plant from position {position}"})
    else:
        return jsonify({"error": f"Failed to remove plant from position {position}"}), 400

@app.route('/api/plants/<int:position>/water', methods=['POST'])
def api_water_plant(position):
    """Trigger watering for a specific plant"""
    plant = plant_config.get_plant_at_position(position)
    if not plant:
        return jsonify({"error": f"No plant found at position {position}"}), 404
    
    # Update watering time
    plant_config.update_watering_time(position)
    plant_config.update_plant_status(position, "active")
    
    # Here you would trigger the actual watering mechanism
    # For now, we'll just log it
    print(f"Watering {plant['name']} at position {position}")
    
    return jsonify({"message": f"Watered {plant['name']} at position {position}"})

@app.route('/api/plants/<int:position>/status')
def api_get_plant_status(position):
    """Get status of a specific plant"""
    plant = plant_config.get_plant_at_position(position)
    if not plant:
        return jsonify({"error": f"No plant found at position {position}"}), 404
    
    # Simulate sensor readings (in real implementation, these would come from actual sensors)
    simulated_readings = {
        "soil_moisture": 45.0,
        "temperature": 22.5,
        "humidity": 60.0,
        "light": 300.0
    }
    
    # Validate readings against plant requirements
    validation_results = {}
    for sensor_type, value in simulated_readings.items():
        validation_results[sensor_type] = plant_config.validate_sensor_reading(position, sensor_type, value)
    
    return jsonify({
        "plant": plant,
        "sensor_readings": simulated_readings,
        "validation": validation_results,
        "needs_water": position in [p["position"] for p in plant_config.get_plants_needing_water()]
    })

@app.route('/api/sensors/readings')
def api_get_sensor_readings():
    """Get current sensor readings for all plants"""
    readings = {}
    for plant in plant_config.config["active_plants"]:
        position = plant["position"]
        # Simulate sensor readings
        readings[position] = {
            "soil_moisture": 45.0,
            "temperature": 22.5,
            "humidity": 60.0,
            "light": 300.0,
            "timestamp": datetime.now().isoformat()
        }
    return jsonify(readings)

@app.route('/api/system/status')
def api_get_system_status():
    """Get overall system status"""
    active_plants = plant_config.config["active_plants"]
    plants_needing_water = plant_config.get_plants_needing_water()
    
    status = {
        "timestamp": datetime.now().isoformat(),
        "total_plants": len(active_plants),
        "plants_needing_water": len(plants_needing_water),
        "sensors": plant_config.config["sensors"],
        "actuators": plant_config.config["actuators"],
        "system": plant_config.config["system"]
    }
    
    return jsonify(status)

@app.route('/api/system/config', methods=['GET', 'POST'])
def api_system_config():
    """Get or update system configuration"""
    if request.method == 'GET':
        return jsonify(plant_config.config)
    
    elif request.method == 'POST':
        data = request.get_json()
        # Update configuration (with validation)
        try:
            plant_config.config.update(data)
            plant_config.save_config()
            return jsonify({"message": "Configuration updated successfully"})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

@app.route('/plants')
def plants_page():
    """Plants management page"""
    active_plants = plant_config.config["active_plants"]
    available_plants = plant_config.list_available_plants()
    return render_template('plants.html', 
                         active_plants=active_plants,
                         available_plants=available_plants)

@app.route('/sensors')
def sensors_page():
    """Sensors monitoring page"""
    return render_template('sensors.html')

@app.route('/config')
def config_page():
    """System configuration page"""
    return render_template('config.html', config=plant_config.config)

# Create templates directory and basic HTML templates
def create_templates():
    """Create basic HTML templates for the web interface"""
    templates_dir = "templates"
    static_dir = "static"
    
    # Create directories
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    
    # Base template
    base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Automated Planter{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .status-active { background-color: #28a745; }
        .status-needs-water { background-color: #ffc107; }
        .status-error { background-color: #dc3545; }
        .plant-card {
            transition: transform 0.2s;
        }
        .plant-card:hover {
            transform: translateY(-2px);
        }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-success">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-seedling"></i> Automated Planter
            </a>
            <div class="navbar-nav">
                <a class="nav-link" href="/">Dashboard</a>
                <a class="nav-link" href="/plants">Plants</a>
                <a class="nav-link" href="/sensors">Sensors</a>
                <a class="nav-link" href="/config">Config</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
    
    # Dashboard template
    dashboard_template = '''{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h1 class="mb-4">
            <i class="fas fa-tachometer-alt"></i> Dashboard
        </h1>
    </div>
</div>

<div class="row mb-4">
    <div class="col-md-3">
        <div class="card bg-primary text-white">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <h4>{{ system_status.total_plants }}</h4>
                        <p class="mb-0">Active Plants</p>
                    </div>
                    <div class="align-self-center">
                        <i class="fas fa-seedling fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-warning text-white">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <h4>{{ system_status.plants_needing_water }}</h4>
                        <p class="mb-0">Need Water</p>
                    </div>
                    <div class="align-self-center">
                        <i class="fas fa-tint fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-info text-white">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <h4>{{ system_status.sensors_enabled }}</h4>
                        <p class="mb-0">Active Sensors</p>
                    </div>
                    <div class="align-self-center">
                        <i class="fas fa-thermometer-half fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-success text-white">
            <div class="card-body">
                <div class="d-flex justify-content-between">
                    <div>
                        <h4>{{ system_status.actuators_enabled }}</h4>
                        <p class="mb-0">Active Actuators</p>
                    </div>
                    <div class="align-self-center">
                        <i class="fas fa-cogs fa-2x"></i>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-seedling"></i> Active Plants</h5>
            </div>
            <div class="card-body">
                {% if active_plants %}
                <div class="row">
                    {% for plant in active_plants %}
                    <div class="col-md-4 mb-3">
                        <div class="card plant-card">
                            <div class="card-body">
                                <h6 class="card-title">
                                    <span class="status-indicator status-active"></span>
                                    {{ plant.name }}
                                </h6>
                                <p class="card-text">
                                    <small class="text-muted">Position: {{ plant.position }}</small><br>
                                    <small class="text-muted">Status: {{ plant.status }}</small>
                                </p>
                                <button class="btn btn-sm btn-primary" onclick="waterPlant({{ plant.position }})">
                                    <i class="fas fa-tint"></i> Water Now
                                </button>
                                <button class="btn btn-sm btn-info" onclick="viewPlantStatus({{ plant.position }})">
                                    <i class="fas fa-info-circle"></i> Status
                                </button>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
                {% else %}
                <div class="text-center py-4">
                    <i class="fas fa-seedling fa-3x text-muted mb-3"></i>
                    <p class="text-muted">No plants configured yet.</p>
                    <a href="/plants" class="btn btn-success">Add Plants</a>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
function waterPlant(position) {
    fetch(`/api/plants/${position}/water`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert(data.message);
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    });
}

function viewPlantStatus(position) {
    fetch(`/api/plants/${position}/status`)
    .then(response => response.json())
    .then(data => {
        if (data.plant) {
            let statusText = `Plant: ${data.plant.name}\\n`;
            statusText += `Position: ${data.plant.position}\\n`;
            statusText += `Status: ${data.plant.status}\\n\\n`;
            statusText += `Sensor Readings:\\n`;
            for (const [sensor, value] of Object.entries(data.sensor_readings)) {
                statusText += `${sensor}: ${value}\\n`;
            }
            alert(statusText);
        } else {
            alert('Error: ' + data.error);
        }
    });
}

// Auto-refresh every 30 seconds
setInterval(() => {
    location.reload();
}, 30000);
</script>
{% endblock %}'''
    
    # Plants template
    plants_template = '''{% extends "base.html" %}

{% block title %}Plants - Automated Planter{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h1 class="mb-4">
            <i class="fas fa-seedling"></i> Plant Management
        </h1>
    </div>
</div>

<div class="row">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-list"></i> Active Plants</h5>
            </div>
            <div class="card-body">
                {% if active_plants %}
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Position</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for plant in active_plants %}
                            <tr>
                                <td>{{ plant.name }}</td>
                                <td>{{ plant.position }}</td>
                                <td>
                                    <span class="status-indicator status-active"></span>
                                    {{ plant.status }}
                                </td>
                                <td>
                                    <button class="btn btn-sm btn-danger" onclick="removePlant({{ plant.position }})">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <p class="text-muted">No plants configured.</p>
                {% endif %}
            </div>
        </div>
    </div>
    
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-plus"></i> Add Plant</h5>
            </div>
            <div class="card-body">
                <form id="addPlantForm">
                    <div class="mb-3">
                        <label for="plantName" class="form-label">Plant Name</label>
                        <select class="form-select" id="plantName" required>
                            <option value="">Select a plant...</option>
                            {% for plant in available_plants %}
                            <option value="{{ plant.name }}">{{ plant.name }}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="position" class="form-label">Position</label>
                        <input type="number" class="form-control" id="position" min="0" max="9" value="0" required>
                    </div>
                    <button type="submit" class="btn btn-success">
                        <i class="fas fa-plus"></i> Add Plant
                    </button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
document.getElementById('addPlantForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const plantName = document.getElementById('plantName').value;
    const position = parseInt(document.getElementById('position').value);
    
    if (!plantName) {
        alert('Please select a plant');
        return;
    }
    
    fetch('/api/plants/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: plantName,
            position: position
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert(data.message);
            location.reload();
        } else {
            alert('Error: ' + data.error);
        }
    });
});

function removePlant(position) {
    if (confirm('Are you sure you want to remove this plant?')) {
        fetch(`/api/plants/remove/${position}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                alert(data.message);
                location.reload();
            } else {
                alert('Error: ' + data.error);
            }
        });
    }
}
</script>
{% endblock %}'''
    
    # Sensors template
    sensors_template = '''{% extends "base.html" %}

{% block title %}Sensors - Automated Planter{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h1 class="mb-4">
            <i class="fas fa-thermometer-half"></i> Sensor Monitoring
        </h1>
    </div>
</div>

<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-chart-line"></i> Real-time Sensor Data</h5>
            </div>
            <div class="card-body">
                <div id="sensorData">
                    <div class="text-center">
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-2">Loading sensor data...</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
function loadSensorData() {
    fetch('/api/sensors/readings')
    .then(response => response.json())
    .then(data => {
        let html = '<div class="row">';
        
        for (const [position, readings] of Object.entries(data)) {
            html += `
                <div class="col-md-4 mb-3">
                    <div class="card">
                        <div class="card-header">
                            <h6>Position ${position}</h6>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-6">
                                    <small class="text-muted">Soil Moisture</small>
                                    <div class="h5">${readings.soil_moisture}%</div>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Temperature</small>
                                    <div class="h5">${readings.temperature}°C</div>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Humidity</small>
                                    <div class="h5">${readings.humidity}%</div>
                                </div>
                                <div class="col-6">
                                    <small class="text-muted">Light</small>
                                    <div class="h5">${readings.light} lux</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        html += '</div>';
        document.getElementById('sensorData').innerHTML = html;
    })
    .catch(error => {
        document.getElementById('sensorData').innerHTML = 
            '<div class="alert alert-danger">Error loading sensor data</div>';
    });
}

// Load data immediately and then every 10 seconds
loadSensorData();
setInterval(loadSensorData, 10000);
</script>
{% endblock %}'''
    
    # Config template
    config_template = '''{% extends "base.html" %}

{% block title %}Configuration - Automated Planter{% endblock %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h1 class="mb-4">
            <i class="fas fa-cogs"></i> System Configuration
        </h1>
    </div>
</div>

<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-code"></i> Configuration JSON</h5>
            </div>
            <div class="card-body">
                <pre><code>{{ config | tojson(indent=2) }}</code></pre>
            </div>
        </div>
    </div>
</div>
{% endblock %}'''
    
    # Write template files
    with open(os.path.join(templates_dir, "base.html"), "w") as f:
        f.write(base_template)
    
    with open(os.path.join(templates_dir, "dashboard.html"), "w") as f:
        f.write(dashboard_template)
    
    with open(os.path.join(templates_dir, "plants.html"), "w") as f:
        f.write(plants_template)
    
    with open(os.path.join(templates_dir, "sensors.html"), "w") as f:
        f.write(sensors_template)
    
    with open(os.path.join(templates_dir, "config.html"), "w") as f:
        f.write(config_template)
    
    print("Templates created successfully!")

if __name__ == "__main__":
    # Create templates
    create_templates()
    
    # Run the web interface
    print("Starting Automated Planter Web Interface...")
    print("Access the interface at: http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)
