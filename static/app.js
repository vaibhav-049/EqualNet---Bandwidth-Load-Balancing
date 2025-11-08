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
                <td><strong>${client.ip}</strong></td>
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
                    <button class="btn-small" onclick="editPriority('${client.ip}', ${client.priority})">
                        Edit
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

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    startUpdateLoop();
});
