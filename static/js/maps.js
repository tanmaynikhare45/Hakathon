// Civic Eye Maps JavaScript
let map;
let markers = [];
let heatmap;
let heatmapData = [];
let markersVisible = true;

// Issue type colors
const issueColors = {
    'pothole': '#ff6b6b',
    'garbage': '#4ecdc4',
    'streetlight': '#45b7d1',
    'waterlogging': '#96ceb4',
    'other': '#ffeaa7'
};

// Issue type icons
const issueIcons = {
    'pothole': 'fas fa-road',
    'garbage': 'fas fa-trash',
    'streetlight': 'fas fa-lightbulb',
    'waterlogging': 'fas fa-tint',
    'other': 'fas fa-exclamation-triangle'
};

function initMap() {
    // Initialize map centered on Pune, India
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 12,
        center: { lat: 18.5204, lng: 73.8567 },
        styles: [
            {
                featureType: 'poi',
                elementType: 'labels',
                stylers: [{ visibility: 'off' }]
            }
        ]
    });
    
    // Hide loading overlay
    document.getElementById('loading-overlay').style.display = 'none';
    
    // Load issues data from API
    loadIssuesFromAPI();
    
    // Update statistics
    updateStatistics();
}

async function loadIssuesFromAPI() {
    try {
        const response = await fetch('/api/reports');
        const issues = await response.json();
        
        // Clear existing markers
        clearMarkers();
        
        issues.forEach(issue => {
            if (issue.location && issue.location.latitude && issue.location.longitude) {
                createMarker({
                    id: issue.report_id,
                    type: issue.issue_type,
                    lat: parseFloat(issue.location.latitude),
                    lng: parseFloat(issue.location.longitude),
                    title: issue.issue_type.charAt(0).toUpperCase() + issue.issue_type.slice(1),
                    description: issue.text || 'No description available',
                    status: issue.status,
                    date: new Date(issue.created_at).toLocaleDateString()
                });
            }
        });
        
        // Initialize heatmap data
        heatmapData = issues
            .filter(issue => issue.location && issue.location.latitude && issue.location.longitude)
            .map(issue => ({
                location: new google.maps.LatLng(
                    parseFloat(issue.location.latitude),
                    parseFloat(issue.location.longitude)
                ),
                weight: 1
            }));
            
    } catch (error) {
        console.error('Error loading issues:', error);
        // Fallback to sample data
        loadSampleData();
    }
}

function loadSampleData() {
    const sampleIssues = [
        {
            id: 1,
            type: 'pothole',
            lat: 18.5204,
            lng: 73.8567,
            title: 'Large Pothole on Main Road',
            description: 'Deep pothole causing traffic issues',
            status: 'pending',
            date: '2025-01-15'
        },
        {
            id: 2,
            type: 'garbage',
            lat: 18.5304,
            lng: 73.8667,
            title: 'Garbage Accumulation',
            description: 'Uncollected garbage for 3 days',
            status: 'in_progress',
            date: '2025-01-14'
        },
        {
            id: 3,
            type: 'streetlight',
            lat: 18.5404,
            lng: 73.8767,
            title: 'Broken Street Light',
            description: 'Street light not working',
            status: 'resolved',
            date: '2025-01-13'
        },
        {
            id: 4,
            type: 'waterlogging',
            lat: 18.5504,
            lng: 73.8867,
            title: 'Waterlogging Issue',
            description: 'Heavy waterlogging after rain',
            status: 'pending',
            date: '2025-01-12'
        },
        {
            id: 5,
            type: 'pothole',
            lat: 18.5604,
            lng: 73.8967,
            title: 'Multiple Potholes',
            description: 'Several potholes on this stretch',
            status: 'in_progress',
            date: '2025-01-11'
        }
    ];
    
    // Clear existing markers
    clearMarkers();
    
    sampleIssues.forEach(issue => {
        createMarker(issue);
    });
    
    // Initialize heatmap data
    heatmapData = sampleIssues.map(issue => ({
        location: new google.maps.LatLng(issue.lat, issue.lng),
        weight: 1
    }));
}

function createMarker(issue) {
    const marker = new google.maps.Marker({
        position: { lat: issue.lat, lng: issue.lng },
        map: map,
        title: issue.title,
        icon: {
            path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
            scale: 6,
            fillColor: issueColors[issue.type] || issueColors.other,
            fillOpacity: 0.9,
            strokeColor: '#ffffff',
            strokeWeight: 2,
            rotation: 0
        }
    });
    
    // Create info window content
    const infoWindowContent = `
        <div style="padding: 10px; max-width: 250px;">
            <h4 style="margin: 0 0 10px 0; color: #333;">
                <i class="${issueIcons[issue.type] || issueIcons.other}" style="color: ${issueColors[issue.type] || issueColors.other};"></i>
                ${issue.title}
            </h4>
            <p style="margin: 0 0 8px 0; color: #666; font-size: 0.9rem;">${issue.description}</p>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                <span style="padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; background: ${getStatusColor(issue.status)}; color: white;">
                    ${issue.status.replace('_', ' ').toUpperCase()}
                </span>
                <span style="font-size: 0.8rem; color: #999;">${issue.date}</span>
            </div>
        </div>
    `;
    
    const infoWindow = new google.maps.InfoWindow({
        content: infoWindowContent
    });
    
    marker.addListener('click', () => {
        infoWindow.open(map, marker);
    });
    
    markers.push(marker);
}

function getStatusColor(status) {
    const colors = {
        'pending': '#ffc107',
        'in_progress': '#17a2b8',
        'resolved': '#28a745',
        'rejected': '#dc3545',
        'submitted': '#6c757d'
    };
    return colors[status] || '#6c757d';
}

function clearMarkers() {
    markers.forEach(marker => {
        marker.setMap(null);
    });
    markers = [];
}

function centerMap() {
    map.setCenter({ lat: 18.5204, lng: 73.8567 });
    map.setZoom(12);
}

function toggleMarkers() {
    markersVisible = !markersVisible;
    markers.forEach(marker => {
        marker.setVisible(markersVisible);
    });
    
    const toggleText = document.getElementById('marker-toggle-text');
    toggleText.textContent = markersVisible ? 'Hide Markers' : 'Show Markers';
}

function showHeatmap() {
    if (heatmap) {
        heatmap.setMap(null);
        heatmap = null;
        return;
    }
    
    heatmap = new google.maps.visualization.HeatmapLayer({
        data: heatmapData,
        map: map,
        radius: 50,
        opacity: 0.6
    });
}

async function updateStatistics() {
    try {
        const response = await fetch('/api/reports');
        const issues = await response.json();
        
        const stats = {
            total: issues.length,
            resolved: issues.filter(issue => issue.status === 'resolved').length,
            pending: issues.filter(issue => issue.status === 'pending' || issue.status === 'submitted').length,
            in_progress: issues.filter(issue => issue.status === 'in_progress').length
        };
        
        document.getElementById('total-issues').textContent = stats.total;
        document.getElementById('resolved-issues').textContent = stats.resolved;
        document.getElementById('pending-issues').textContent = stats.pending;
        document.getElementById('in-progress-issues').textContent = stats.in_progress;
        
    } catch (error) {
        console.error('Error loading statistics:', error);
        // Fallback to sample data
        const sampleStats = {
            total: 5,
            resolved: 1,
            pending: 2,
            in_progress: 2
        };
        
        document.getElementById('total-issues').textContent = sampleStats.total;
        document.getElementById('resolved-issues').textContent = sampleStats.resolved;
        document.getElementById('pending-issues').textContent = sampleStats.pending;
        document.getElementById('in-progress-issues').textContent = sampleStats.in_progress;
    }
}

// Handle window resize
window.addEventListener('resize', () => {
    if (map) {
        google.maps.event.trigger(map, 'resize');
    }
});