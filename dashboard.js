// Dashboard JavaScript functionality
let conversationsChart = null;
let backgroundChart = null;

document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadPrograms();
    
    // Refresh data every 5 minutes
    setInterval(loadStats, 5 * 60 * 1000);
});

async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.status === 'success') {
            updateConversationsChart(data.daily_conversations);
            updateBackgroundChart(data.user_backgrounds);
        } else {
            console.error('Error loading stats:', data.message);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadPrograms() {
    try {
        const response = await fetch('/api/programs');
        const data = await response.json();
        
        if (data.status === 'success') {
            displayPrograms(data.programs);
        } else {
            document.getElementById('programsInfo').innerHTML = 
                `<div class="alert alert-danger">Ошибка загрузки программ: ${data.message}</div>`;
        }
    } catch (error) {
        document.getElementById('programsInfo').innerHTML = 
            `<div class="alert alert-danger">Ошибка загрузки программ: ${error.message}</div>`;
    }
}

function updateConversationsChart(dailyData) {
    const ctx = document.getElementById('conversationsChart').getContext('2d');
    
    if (conversationsChart) {
        conversationsChart.destroy();
    }
    
    const labels = dailyData.map(item => {
        const date = new Date(item.date);
        return date.toLocaleDateString('ru-RU', { month: 'short', day: 'numeric' });
    });
    
    const data = dailyData.map(item => item.conversations);
    
    conversationsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Разговоры',
                data: data,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: 'white'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: 'white'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: 'white'
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    }
                }
            }
        }
    });
}

function updateBackgroundChart(backgroundData) {
    const ctx = document.getElementById('backgroundChart').getContext('2d');
    
    if (backgroundChart) {
        backgroundChart.destroy();
    }
    
    const labels = backgroundData.map(item => {
        const backgroundNames = {
            'technical': 'Технический',
            'product': 'Продуктовый',
            'mixed': 'Смешанный',
            'beginner': 'Начинающий',
            'unknown': 'Не указан'
        };
        return backgroundNames[item.background] || item.background;
    });
    
    const data = backgroundData.map(item => item.count);
    
    const colors = [
        'rgba(255, 99, 132, 0.8)',
        'rgba(54, 162, 235, 0.8)',
        'rgba(255, 205, 86, 0.8)',
        'rgba(75, 192, 192, 0.8)',
        'rgba(153, 102, 255, 0.8)'
    ];
    
    backgroundChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderColor: colors.map(color => color.replace('0.8', '1')),
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: 'white',
                        padding: 10,
                        font: {
                            size: 12
                        }
                    }
                }
            }
        }
    });
}

function displayPrograms(programs) {
    const programsContainer = document.getElementById('programsInfo');
    
    if (programs.length === 0) {
        programsContainer.innerHTML = `
            <div class="text-center text-muted">
                <i class="fas fa-exclamation-circle fa-3x mb-3"></i>
                <p>Программы не найдены. Нажмите "Обновить данные" для загрузки.</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="row">';
    
    programs.forEach(program => {
        html += `
            <div class="col-lg-6 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">
                            <i class="fas fa-graduation-cap me-2"></i>
                            ${program.name}
                        </h5>
                        <p class="card-text text-muted">${program.description || 'Описание отсутствует'}</p>
                        
                        <div class="row text-center mb-3">
                            <div class="col-4">
                                <div class="border-end">
                                    <h6 class="text-primary mb-0">${program.budget_places || 0}</h6>
                                    <small class="text-muted">Бюджет</small>
                                </div>
                            </div>
                            <div class="col-4">
                                <div class="border-end">
                                    <h6 class="text-success mb-0">${program.contract_places || 0}</h6>
                                    <small class="text-muted">Контракт</small>
                                </div>
                            </div>
                            <div class="col-4">
                                <h6 class="text-info mb-0">${program.duration || 'N/A'}</h6>
                                <small class="text-muted">Срок</small>
                            </div>
                        </div>
                        
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">
                                <i class="fas fa-money-bill-wave me-1"></i>
                                ${program.cost || 'Не указана'}
                            </small>
                            <small class="text-muted">
                                Обновлено: ${program.updated_at ? new Date(program.updated_at).toLocaleDateString('ru-RU') : 'N/A'}
                            </small>
                        </div>
                        
                        <div class="mt-2">
                            <a href="${program.url}" target="_blank" class="btn btn-outline-primary btn-sm">
                                <i class="fas fa-external-link-alt me-1"></i>
                                Открыть страницу
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    programsContainer.innerHTML = html;
}

// Utility function to format numbers
function formatNumber(num) {
    return new Intl.NumberFormat('ru-RU').format(num);
}

// Error handling for charts
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.color = 'white';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
