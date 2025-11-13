const API_URL = 'http://localhost:5000/api';

let trafficChart = null;
let distributionChart = null;

let currentEditIP = null;

function initCharts() {
    const trafficCtx = document.getElementById('trafficChart').getContext('2d');
    
    const uploadGradient = trafficCtx.createLinearGradient(0, 0, 0, 300);
    uploadGradient.addColorStop(0, 'rgba(0, 212, 255, 0.8)');
    uploadGradient.addColorStop(1, 'rgba(0, 212, 255, 0.1)');
    
    const downloadGradient = trafficCtx.createLinearGradient(0, 0, 0, 300);
    downloadGradient.addColorStop(0, 'rgba(255, 107, 157, 0.8)');
    downloadGradient.addColorStop(1, 'rgba(255, 107, 157, 0.1)');
    
    trafficChart = new Chart(trafficCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Upload (KB/s)',
                    data: [],
                    borderColor: '#00d4ff',
                    backgroundColor: uploadGradient,
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointBackgroundColor: '#00d4ff',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 6
                },
                {
                    label: 'Download (KB/s)',
                    data: [],
                    borderColor: '#ff6b9d',
                    backgroundColor: downloadGradient,
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointBackgroundColor: '#ff6b9d',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(10, 10, 31, 0.9)',
                    titleColor: '#00d4ff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.parsed.y.toFixed(2) + ' KB/s';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        font: {
                            size: 11
                        }
                    }
                },
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    },
                    ticks: {
                        color: 'rgba(255, 255, 255, 0.7)',
                        font: {
                            size: 11
                        },
                        maxRotation: 0
                    }
                }
            }
        }
    });

    const distCtx = document.getElementById('distributionChart').getContext('2d');
    distributionChart = new Chart(distCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#00d4ff', '#ff6b9d', '#00ff88', '#ffd56b',
                    '#c364ff', '#4facfe', '#43e97b', '#fa709a',
                    '#fee140', '#30cfd0', '#a8edea', '#fed6e3'
                ],
                borderWidth: 3,
                borderColor: 'rgba(10, 10, 31, 0.8)',
                hoverBorderWidth: 5,
                hoverBorderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'right',
                    labels: {
                        color: 'rgba(255, 255, 255, 0.9)',
                        font: {
                            size: 11
                        },
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(10, 10, 31, 0.9)',
                    titleColor: '#00d4ff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(255, 255, 255, 0.2)',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return label + ': ' + value + ' Mbps (' + percentage + '%)';
                        }
                    }
                }
            }
        }
    });
}

async function updateStatus() {
    try {
        const response = await fetch(`${API_URL}/status`);
        const data = await response.json();
        
        document.getElementById('total-clients').textContent = data.total_clients;
        document.getElementById('upload-speed').textContent = data.network_stats.sent + ' KB/s';
        document.getElementById('download-speed').textContent = data.network_stats.recv + ' KB/s';
        document.getElementById('total-bandwidth').textContent = data.total_bandwidth + ' Mbps';
        
        updateLastUpdate();
    } catch (error) {
        console.error('Error updating status:', error);
    }
}

async function updateClientsTable() {
    try {
        const response = await fetch(`${API_URL}/clients`);
        const clients = await response.json();
        
        const tbody = document.getElementById('clients-tbody');
        
        if (clients.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">No clients connected</td></tr>';
            return;
        }
        
        tbody.innerHTML = clients.map(client => `
            <tr>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 20px;">${client.icon || '📱'}</span>
                        <div>
                            <strong>${client.friendly_name || client.ip}</strong>
                            <br>
                            <small style="color: rgba(255,255,255,0.6); font-size: 11px;">${client.ip}</small>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="badge ${getPriorityClass(client.priority)}">
                        ${client.priority}
                    </span>
                </td>
                <td>${client.usage} Mbps</td>
                <td>${client.allocated} Mbps</td>
                <td>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${Math.min(client.usage_percent, 100)}%"></div>
                    </div>
                    ${client.usage_percent}%
                </td>
                <td>
                    <button class="btn-small" onclick="editPriority('${client.ip}', ${client.priority})" style="margin: 2px;">
                        📝 Edit
                    </button>
                    <button class="btn-small" onclick="editDeviceName('${client.ip}')" style="margin: 2px; background: #4caf50;">
                        🏷️ Rename
                    </button>
                </td>
            </tr>
        `).join('');
        
        updateDistributionChart(clients);
        
    } catch (error) {
        console.error('Error updating clients:', error);
    }
}

async function updateTrafficChart() {
    try {
        const response = await fetch(`${API_URL}/history`);
        const history = await response.json();
        
        trafficChart.data.labels = history.time;
        trafficChart.data.datasets[0].data = history.upload;
        trafficChart.data.datasets[1].data = history.download;
        trafficChart.update('none');
        
    } catch (error) {
        console.error('Error updating traffic chart:', error);
    }
}

function updateDistributionChart(clients) {
    const labels = clients.map(c => c.ip);
    const data = clients.map(c => c.allocated);
    
    distributionChart.data.labels = labels;
    distributionChart.data.datasets[0].data = data;
    distributionChart.update('none');
}

function getPriorityClass(priority) {
    if (priority >= 7) return 'badge-high';
    if (priority >= 4) return 'badge-medium';
    return 'badge-low';
}

async function updateBandwidth() {
    const bandwidth = document.getElementById('bandwidth-slider').value;
    
    try {
        const response = await fetch(`${API_URL}/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                total_bandwidth: parseInt(bandwidth)
            })
        });
        
        if (response.ok) {
            showNotification('Bandwidth updated successfully!');
        }
    } catch (error) {
        console.error('Error updating bandwidth:', error);
        showNotification('Failed to update bandwidth', 'error');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const slider = document.getElementById('bandwidth-slider');
    const valueDisplay = document.getElementById('bandwidth-value');
    
    slider.addEventListener('input', (e) => {
        valueDisplay.textContent = e.target.value;
    });
});

function editPriority(ip, currentPriority) {
    currentEditIP = ip;
    document.getElementById('modal-ip').textContent = ip;
    document.getElementById('modal-priority').value = currentPriority;
    document.getElementById('priority-modal').style.display = 'block';
}

function closeModal() {
    document.getElementById('priority-modal').style.display = 'none';
    currentEditIP = null;
}

async function savePriority() {
    const priority = document.getElementById('modal-priority').value;
    
    try {
        const response = await fetch(`${API_URL}/priority/${currentEditIP}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                priority: parseInt(priority)
            })
        });
        
        if (response.ok) {
            showNotification('Priority updated successfully!');
            closeModal();
        }
    } catch (error) {
        console.error('Error updating priority:', error);
        showNotification('Failed to update priority', 'error');
    }
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'success' ? '#4caf50' : '#f44336'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function updateLastUpdate() {
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    document.getElementById('last-update').textContent = timeString;
}

window.onclick = function(event) {
    const modal = document.getElementById('priority-modal');
    if (event.target === modal) {
        closeModal();
    }
}

function startUpdateLoop() {
    updateStatus();
    updateClientsTable();
    updateTrafficChart();
    
    setInterval(() => {
        updateStatus();
        updateClientsTable();
        updateTrafficChart();
    }, 2000);
}

// CSV Export Functions
async function exportCSV(type, hours) {
    try {
        let url;
        if (type === 'bandwidth') {
            url = `${API_URL}/export/csv/bandwidth?hours=${hours}`;
        } else if (type === 'clients') {
            url = `${API_URL}/export/csv/clients?hours=${hours}`;
        } else if (type === 'alerts') {
            url = `${API_URL}/export/csv/alerts?limit=${hours}`;
        } else if (type === 'full-report') {
            url = `${API_URL}/export/csv/full-report?hours=${hours}`;
        }
        
        // Trigger download
        window.open(url, '_blank');
        showNotification('📥 Downloading CSV file...', 'success');
    } catch (error) {
        console.error('Error exporting CSV:', error);
        showNotification('Failed to export CSV', 'error');
    }
}

// Device Naming Functions
async function editDeviceName(ip) {
    const currentName = await getDeviceLabel(ip);
    const newName = prompt(`Enter custom name for device ${ip}:`, currentName);
    
    if (newName && newName.trim() !== '') {
        try {
            const response = await fetch(`${API_URL}/device/${ip}/label`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    label: newName.trim()
                })
            });
            
            const data = await response.json();
            if (data.success) {
                showNotification(`✓ Device renamed to: ${newName}`, 'success');
                updateClientsTable(); // Refresh the display
            } else {
                showNotification('Failed to rename device', 'error');
            }
        } catch (error) {
            console.error('Error renaming device:', error);
            showNotification('Failed to rename device', 'error');
        }
    }
}

async function getDeviceLabel(ip) {
    try {
        const response = await fetch(`${API_URL}/device/${ip}/label`);
        const data = await response.json();
        return data.label || ip;
    } catch (error) {
        console.error('Error getting device label:', error);
        return ip;
    }
}

// Alert Threshold Function
async function updateAlertThreshold() {
    const threshold = document.getElementById('high-usage-threshold').value;
    
    try {
        const response = await fetch(`${API_URL}/alerts/threshold`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                threshold: parseFloat(threshold)
            })
        });
        
        const data = await response.json();
        if (data.success) {
            showNotification(`✓ High usage threshold set to ${threshold}%`, 'success');
        } else {
            showNotification('Failed to update threshold', 'error');
        }
    } catch (error) {
        console.error('Error updating threshold:', error);
        showNotification('Failed to update threshold', 'error');
    }
}

// Update threshold slider value display
document.addEventListener('DOMContentLoaded', () => {
    const thresholdSlider = document.getElementById('high-usage-threshold');
    const thresholdValue = document.getElementById('threshold-value');
    
    if (thresholdSlider && thresholdValue) {
        thresholdSlider.addEventListener('input', function() {
            thresholdValue.textContent = this.value;
        });
    }
});

// Router Control Functions
async function loadRouterInfo() {
    try {
        const response = await fetch(`${API_URL}/router/info`);
        const data = await response.json();
        
        document.getElementById('router-ip').textContent = data.ip || 'N/A';
        document.getElementById('router-type').textContent = data.type || 'unknown';
        document.getElementById('router-mode').textContent = data.mode || 'unknown';
        
        const statusBadge = document.getElementById('router-status');
        
        // Update status based on control mode
        if (data.mode === 'hotspot') {
            if (data.status === 'ready' && data.admin) {
                statusBadge.textContent = '✅ Hotspot Active (QoS Ready)';
                statusBadge.style.background = 'rgba(76, 175, 80, 0.2)';
                statusBadge.style.color = '#4caf50';
            } else if (!data.admin) {
                statusBadge.textContent = '⚠️ Need Admin Rights';
                statusBadge.style.background = 'rgba(255, 152, 0, 0.2)';
                statusBadge.style.color = '#ff9800';
            } else {
                statusBadge.textContent = '🔵 Hotspot Mode';
                statusBadge.style.background = 'rgba(33, 150, 243, 0.2)';
                statusBadge.style.color = '#2196f3';
            }
        } else if (data.mode === 'simulation' || data.mode === 'router') {
            statusBadge.textContent = '🔹 Router Mode (Simulation)';
            statusBadge.style.background = 'rgba(255, 193, 7, 0.2)';
            statusBadge.style.color = '#ffc107';
        } else {
            statusBadge.textContent = '❌ Unknown Mode';
            statusBadge.style.background = 'rgba(244, 67, 54, 0.2)';
            statusBadge.style.color = '#f44336';
        }
    } catch (error) {
        console.error('Error loading router info:', error);
        document.getElementById('router-status').textContent = '❌ Error';
    }
}

async function applyLimitsToRouter() {
    const resultDiv = document.getElementById('router-result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<p style="color: #ffc107;">⏳ Applying limits to router...</p>';
    
    try {
        const response = await fetch(`${API_URL}/router/apply_limits`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            resultDiv.innerHTML = `
                <p style="color: #4caf50;">
                    ✅ ${data.message}<br>
                    Applied: ${data.applied}/${data.total} devices
                </p>
            `;
            showNotification(`✓ Limits applied to ${data.applied} devices`, 'success');
        } else {
            resultDiv.innerHTML = `<p style="color: #f44336;">❌ Failed: ${data.error}</p>`;
            showNotification('Failed to apply limits', 'error');
        }
    } catch (error) {
        console.error('Error applying limits:', error);
        resultDiv.innerHTML = `<p style="color: #f44336;">❌ Error: ${error.message}</p>`;
        showNotification('Error applying limits', 'error');
    }
    
    setTimeout(() => {
        resultDiv.style.display = 'none';
    }, 5000);
}

async function clearRouterLimits() {
    if (!confirm('Clear all bandwidth limits from router?')) {
        return;
    }
    
    const resultDiv = document.getElementById('router-result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = '<p style="color: #ffc107;">⏳ Clearing limits...</p>';
    
    try {
        const response = await fetch(`${API_URL}/router/clear_limits`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            resultDiv.innerHTML = '<p style="color: #4caf50;">✅ All limits cleared</p>';
            showNotification('✓ All limits cleared from router', 'success');
        } else {
            resultDiv.innerHTML = `<p style="color: #f44336;">❌ Failed: ${data.error}</p>`;
            showNotification('Failed to clear limits', 'error');
        }
    } catch (error) {
        console.error('Error clearing limits:', error);
        resultDiv.innerHTML = `<p style="color: #f44336;">❌ Error: ${error.message}</p>`;
        showNotification('Error clearing limits', 'error');
    }
    
    setTimeout(() => {
        resultDiv.style.display = 'none';
    }, 5000);
}

async function applyPriorityToRouter(ip, priority) {
    try {
        const response = await fetch(`${API_URL}/router/set_priority/${ip}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({priority: priority})
        });
        const data = await response.json();
        
        if (data.success) {
            console.log(`✅ Priority P${priority} applied to router for ${ip}`);
        }
    } catch (error) {
        console.error('Error applying priority to router:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    startUpdateLoop();
    loadRouterInfo();
});

