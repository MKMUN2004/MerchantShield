/**
 * Enhanced Merchant Verification System
 * Dashboard JavaScript
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Risk Level Distribution Chart
    if (document.getElementById('riskLevelChart')) {
        const riskLevelCtx = document.getElementById('riskLevelChart').getContext('2d');
        
        // Create the risk level chart with the data passed from the template
        const riskLevelChart = new Chart(riskLevelCtx, {
            type: 'doughnut',
            data: {
                labels: riskLevelLabels,
                datasets: [{
                    data: riskLevelCounts,
                    backgroundColor: [
                        '#1cc88a', // Low - Green
                        '#4e73df', // Medium - Blue
                        '#f6c23e', // High - Yellow
                        '#e74a3b'  // Extreme - Red
                    ],
                    hoverBackgroundColor: [
                        '#17a673',
                        '#2e59d9',
                        '#dda20a',
                        '#be3024'
                    ],
                    hoverBorderColor: "rgba(234, 236, 244, 1)",
                }]
            },
            options: {
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }

    // Business Type Distribution Chart
    if (document.getElementById('businessTypeChart')) {
        const businessTypeCtx = document.getElementById('businessTypeChart').getContext('2d');
        
        // Create the business type chart with the data passed from the template
        const businessTypeChart = new Chart(businessTypeCtx, {
            type: 'bar',
            data: {
                labels: businessTypeLabels,
                datasets: [{
                    label: 'Number of Merchants',
                    data: businessTypeCounts,
                    backgroundColor: '#4e73df',
                    hoverBackgroundColor: '#2e59d9',
                    borderColor: '#4e73df',
                    borderWidth: 1
                }]
            },
            options: {
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: "rgba(0, 0, 0, 0.05)"
                        },
                        ticks: {
                            precision: 0
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    // Verification Status Distribution (Verified, Pending, Flagged, Rejected)
    if (document.getElementById('statusChart')) {
        const statusCtx = document.getElementById('statusChart').getContext('2d');
        
        // Create the status chart (assumes these variables are passed from the view)
        const statusChart = new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: ['Verified', 'Pending', 'Flagged', 'Rejected'],
                datasets: [{
                    data: [verified_merchants, pending_merchants, flagged_merchants, rejected_merchants],
                    backgroundColor: [
                        '#1cc88a', // Verified - Green
                        '#36b9cc', // Pending - Info/Blue
                        '#f6c23e', // Flagged - Yellow
                        '#e74a3b'  // Rejected - Red
                    ],
                    hoverBackgroundColor: [
                        '#17a673',
                        '#2c9faf',
                        '#dda20a',
                        '#be3024'
                    ],
                    hoverBorderColor: "rgba(234, 236, 244, 1)",
                }]
            },
            options: {
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }
    
    // Merchants Added Over Time (if data is available)
    if (document.getElementById('merchantsTimelineChart')) {
        const timelineCtx = document.getElementById('merchantsTimelineChart').getContext('2d');
        
        // Assumes monthlyMerchantData is passed from the template
        if (typeof monthlyMerchantData !== 'undefined') {
            const labels = monthlyMerchantData.map(item => item.month);
            const counts = monthlyMerchantData.map(item => item.count);
            
            const timelineChart = new Chart(timelineCtx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'New Merchants',
                        data: counts,
                        borderColor: '#4e73df',
                        backgroundColor: 'rgba(78, 115, 223, 0.05)',
                        pointBackgroundColor: '#4e73df',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '#4e73df',
                        tension: 0.3,
                        fill: true
                    }]
                },
                options: {
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: "rgba(0, 0, 0, 0.05)"
                            },
                            ticks: {
                                precision: 0
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
        }
    }
    
    // Update the dashboard data periodically (every 30 seconds)
    if (document.querySelector('.dashboard-container')) {
        setInterval(function() {
            updateDashboardStats();
        }, 30000);
    }
});

/**
 * Fetches updated dashboard statistics from the API
 */
function updateDashboardStats() {
    fetch('/api/dashboard/stats/')
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch dashboard stats');
            }
            return response.json();
        })
        .then(data => {
            // Update the count displays
            document.getElementById('totalMerchantsCount').textContent = data.total_merchants;
            document.getElementById('verifiedMerchantsCount').textContent = data.verified_merchants;
            document.getElementById('flaggedMerchantsCount').textContent = data.flagged_merchants;
            document.getElementById('pendingMerchantsCount').textContent = data.pending_merchants;
            document.getElementById('highRiskMerchantsCount').textContent = data.high_risk_merchants;
            document.getElementById('openFlagsCount').textContent = data.open_flags;
        })
        .catch(error => {
            console.error('Error updating dashboard stats:', error);
        });
}

/**
 * Formats a number with commas for thousands separators
 */
function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Handle dashboard date range picker (if present)
 */
if (document.getElementById('dateRangePicker')) {
    const dateRangePicker = document.getElementById('dateRangePicker');
    
    dateRangePicker.addEventListener('change', function() {
        const selectedRange = this.value;
        window.location.href = `/?date_range=${selectedRange}`;
    });
}
