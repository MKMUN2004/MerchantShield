/**
 * Enhanced Merchant Verification System
 * Main JavaScript Functions
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize DataTables
    if ($.fn.dataTable) {
        $('.dataTable').each(function() {
            if (!$.fn.DataTable.isDataTable(this)) {
                $(this).DataTable({
                    "language": {
                        "paginate": {
                            "previous": "<i class='fas fa-chevron-left'></i>",
                            "next": "<i class='fas fa-chevron-right'></i>"
                        }
                    }
                });
            }
        });
    }
    
    // Initialize tooltips
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Handle confirmation dialogs
    const confirmButtons = document.querySelectorAll('.confirm-action');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const confirmMessage = this.getAttribute('data-confirm') || 'Are you sure you want to perform this action?';
            if (!confirm(confirmMessage)) {
                e.preventDefault();
                return false;
            }
        });
    });
    
    // Handle merchant verification form
    const merchantForm = document.getElementById('merchantVerificationForm');
    if (merchantForm) {
        merchantForm.addEventListener('submit', function(e) {
            const statusField = document.getElementById('id_status');
            const riskLevelField = document.getElementById('id_risk_level');
            
            // Validate required fields
            if (!statusField.value) {
                e.preventDefault();
                alert('Please select a verification status.');
                statusField.focus();
                return false;
            }
            
            if (!riskLevelField.value) {
                e.preventDefault();
                alert('Please select a risk level.');
                riskLevelField.focus();
                return false;
            }
            
            // Confirm rejection
            if (statusField.value === 'rejected') {
                if (!confirm('Are you sure you want to reject this merchant? This will prevent them from processing transactions.')) {
                    e.preventDefault();
                    return false;
                }
            }
        });
    }
    
    // Handle flag resolution form
    const resolveForm = document.getElementById('resolveFlag');
    if (resolveForm) {
        resolveForm.addEventListener('submit', function(e) {
            const statusField = document.getElementById('id_status');
            const notesField = document.getElementById('id_resolution_notes');
            
            if (!statusField.value) {
                e.preventDefault();
                alert('Please select a resolution status.');
                statusField.focus();
                return false;
            }
            
            if (!notesField.value.trim()) {
                e.preventDefault();
                alert('Please provide resolution notes.');
                notesField.focus();
                return false;
            }
        });
    }
    
    // Handle live search functionality
    const searchInput = document.getElementById('quickSearch');
    if (searchInput) {
        let searchTimer;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimer);
            const query = this.value.trim();
            
            // Wait for user to finish typing
            searchTimer = setTimeout(function() {
                if (query.length >= 2) {
                    performSearch(query);
                } else {
                    clearSearchResults();
                }
            }, 300);
        });
    }
    
    // Filter toggle button
    const filterToggleBtn = document.getElementById('filterToggle');
    if (filterToggleBtn) {
        filterToggleBtn.addEventListener('click', function() {
            const filterForm = document.getElementById('filterForm');
            if (filterForm.classList.contains('show')) {
                filterForm.classList.remove('show');
                this.innerHTML = '<i class="fas fa-filter"></i> Show Filters';
            } else {
                filterForm.classList.add('show');
                this.innerHTML = '<i class="fas fa-filter"></i> Hide Filters';
            }
        });
    }
    
    // Initialize any risk gauge charts
    initRiskGauges();
    
    // Add click handler for tabs
    const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabButtons.forEach(button => {
        button.addEventListener('shown.bs.tab', function(e) {
            const targetId = e.target.getAttribute('href');
            localStorage.setItem('activeTab', targetId);
        });
    });
    
    // Restore active tab from localStorage
    const activeTab = localStorage.getItem('activeTab');
    if (activeTab) {
        const tab = document.querySelector(`[href="${activeTab}"]`);
        if (tab) {
            const bsTab = new bootstrap.Tab(tab);
            bsTab.show();
        }
    }
});

/**
 * Initialize risk gauge charts
 */
function initRiskGauges() {
    document.querySelectorAll('.risk-gauge').forEach(gaugeElement => {
        const score = parseFloat(gaugeElement.getAttribute('data-score'));
        const ctx = gaugeElement.getContext('2d');
        
        if (isNaN(score)) return;
        
        // Determine color based on risk score
        let color;
        if (score >= 4) {
            color = '#e74a3b'; // Red/Extreme
        } else if (score >= 3) {
            color = '#f6c23e'; // Yellow/High
        } else if (score >= 2) {
            color = '#4e73df'; // Blue/Medium
        } else {
            color = '#1cc88a'; // Green/Low
        }
        
        // Create gauge chart
        new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [score, 5 - score],
                    backgroundColor: [color, '#eaecf4'],
                    borderWidth: 0
                }]
            },
            options: {
                cutout: '70%',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                }
            },
            plugins: [{
                id: 'centerText',
                afterDraw: function(chart) {
                    const width = chart.width;
                    const height = chart.height;
                    const ctx = chart.ctx;
                    
                    ctx.restore();
                    const fontSize = (height / 114).toFixed(2);
                    ctx.font = fontSize + "em sans-serif";
                    ctx.textBaseline = "middle";
                    
                    const text = score.toFixed(1);
                    const textX = Math.round((width - ctx.measureText(text).width) / 2);
                    const textY = height / 2;
                    
                    ctx.fillStyle = color;
                    ctx.fillText(text, textX, textY);
                    ctx.save();
                }
            }]
        });
    });
}

/**
 * Perform merchant search using API
 */
function performSearch(query) {
    const resultsContainer = document.getElementById('searchResults');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Searching...</div>';
    
    fetch(`/api/merchants/?name=${encodeURIComponent(query)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Search request failed');
            }
            return response.json();
        })
        .then(data => {
            displaySearchResults(data, resultsContainer);
        })
        .catch(error => {
            console.error('Error performing search:', error);
            resultsContainer.innerHTML = '<div class="alert alert-danger">Error performing search. Please try again.</div>';
        });
}

/**
 * Display search results in the container
 */
function displaySearchResults(data, container) {
    if (!data || data.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No merchants found matching your search.</div>';
        return;
    }
    
    let html = '<div class="list-group">';
    
    data.forEach(merchant => {
        // Determine badge class based on status
        let statusBadgeClass = '';
        if (merchant.status === 'verified') {
            statusBadgeClass = 'bg-success';
        } else if (merchant.status === 'flagged') {
            statusBadgeClass = 'bg-warning';
        } else if (merchant.status === 'rejected') {
            statusBadgeClass = 'bg-danger';
        } else {
            statusBadgeClass = 'bg-info';
        }
        
        html += `
            <a href="/merchants/${merchant.id}/" class="list-group-item list-group-item-action">
                <div class="d-flex w-100 justify-content-between">
                    <h5 class="mb-1">${merchant.name}</h5>
                    <span class="badge ${statusBadgeClass}">${merchant.status_display}</span>
                </div>
                <p class="mb-1">${merchant.business_type_display} - ${merchant.country || 'Unknown Location'}</p>
                <small>Registration: ${merchant.registration_number}</small>
            </a>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Clear search results
 */
function clearSearchResults() {
    const resultsContainer = document.getElementById('searchResults');
    if (resultsContainer) {
        resultsContainer.innerHTML = '';
    }
}

/**
 * Load merchant verification data from API
 */
function loadMerchantVerificationData(merchantId) {
    if (!merchantId) return;
    
    const verificationContainer = document.getElementById('verificationData');
    if (!verificationContainer) return;
    
    verificationContainer.innerHTML = '<div class="text-center p-4"><i class="fas fa-spinner fa-spin"></i> Loading verification data...</div>';
    
    fetch(`/api/merchants/${merchantId}/verify/`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load verification data');
            }
            return response.json();
        })
        .then(data => {
            displayVerificationData(data, verificationContainer);
        })
        .catch(error => {
            console.error('Error loading verification data:', error);
            verificationContainer.innerHTML = '<div class="alert alert-danger">Error loading verification data. Please try again.</div>';
        });
}

/**
 * Display merchant verification data
 */
function displayVerificationData(data, container) {
    // This would generate a detailed verification view from API data
    // For real implementation, this would create UI elements showing risk assessment, external verification, etc.
    let html = '<div class="row">';
    
    // Risk assessment section
    html += `
        <div class="col-md-6 mb-4">
            <div class="card h-100">
                <div class="card-header">
                    <h5 class="m-0 font-weight-bold text-primary">Risk Assessment</h5>
                </div>
                <div class="card-body">
                    <div class="row align-items-center">
                        <div class="col-md-6">
                            <h4>Risk Score: ${data.risk_assessment.risk_score.toFixed(2)}</h4>
                            <p>Level: ${data.risk_assessment.risk_level}</p>
                        </div>
                        <div class="col-md-6">
                            <canvas class="risk-gauge" data-score="${data.risk_assessment.risk_score}" width="100" height="100"></canvas>
                        </div>
                    </div>
                    
                    <h5 class="mt-3">Risk Factors</h5>
                    <ul>
    `;
    
    // Add risk factors
    for (const [factor, score] of Object.entries(data.risk_assessment.risk_factors)) {
        html += `<li>${factor.replace('_', ' ')}: ${score.toFixed(2)}</li>`;
    }
    
    html += `
                    </ul>
                </div>
            </div>
        </div>
    `;
    
    // External verification section
    html += `
        <div class="col-md-6 mb-4">
            <div class="card h-100">
                <div class="card-header">
                    <h5 class="m-0 font-weight-bold text-primary">External Verification</h5>
                </div>
                <div class="card-body">
                    <p>Status: ${data.external_verification.verification_status}</p>
                    <p>Confidence: ${data.external_verification.confidence_score.toFixed(2)}</p>
                    
                    <h5 class="mt-3">Verification Results</h5>
                    <pre class="bg-light p-2" style="height: 200px; overflow-y: auto;">${JSON.stringify(data.external_verification, null, 2)}</pre>
                </div>
            </div>
        </div>
    `;
    
    html += '</div>';
    
    container.innerHTML = html;
    
    // Initialize risk gauges
    initRiskGauges();
}

/**
 * Analyze transaction patterns
 */
function analyzeTransactions(merchantId) {
    if (!merchantId) return;
    
    const container = document.getElementById('transactionAnalysis');
    if (!container) return;
    
    container.innerHTML = '<div class="text-center p-4"><i class="fas fa-spinner fa-spin"></i> Analyzing transactions...</div>';
    
    fetch(`/api/merchants/${merchantId}/transactions/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Transaction analysis failed');
            }
            return response.json();
        })
        .then(data => {
            displayTransactionAnalysis(data, container);
        })
        .catch(error => {
            console.error('Error analyzing transactions:', error);
            container.innerHTML = '<div class="alert alert-danger">Error analyzing transactions. Please try again.</div>';
        });
}

/**
 * Display transaction analysis results
 */
function displayTransactionAnalysis(data, container) {
    // Create HTML to display transaction analysis results
    // In a real implementation, this would include charts and detailed breakdowns
    let html = `
        <div class="card shadow mb-4">
            <div class="card-header py-3">
                <h6 class="m-0 font-weight-bold text-primary">Transaction Analysis Results</h6>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <table class="table table-sm">
                            <tr>
                                <th>Average Transaction:</th>
                                <td>$${data.average_transaction_amount.toFixed(2)}</td>
                            </tr>
                            <tr>
                                <th>Monthly Volume:</th>
                                <td>${data.monthly_transaction_volume}</td>
                            </tr>
                            <tr>
                                <th>High-Risk Countries:</th>
                                <td>${data.high_risk_countries_percentage.toFixed(1)}%</td>
                            </tr>
                            <tr>
                                <th>Unusual Hours:</th>
                                <td>${data.unusual_hours_percentage.toFixed(1)}%</td>
                            </tr>
                            <tr>
                                <th>Similar Transactions:</th>
                                <td>${data.similar_transactions_percentage.toFixed(1)}%</td>
                            </tr>
                            <tr>
                                <th>Chargeback Rate:</th>
                                <td>${data.chargeback_rate.toFixed(2)}%</td>
                            </tr>
                        </table>
                    </div>
                    <div class="col-md-6">
                        <canvas id="transactionChart" width="100%" height="200"></canvas>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Create transaction chart if data is available
    if (data.detailed_data && data.detailed_data.country_distribution) {
        const ctx = document.getElementById('transactionChart').getContext('2d');
        
        const countries = Object.keys(data.detailed_data.country_distribution);
        const counts = Object.values(data.detailed_data.country_distribution);
        
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: countries,
                datasets: [{
                    data: counts,
                    backgroundColor: [
                        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
                        '#6f42c1', '#20c9a6', '#5a5c69', '#858796', '#dddfeb'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            font: {
                                size: 10
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Transaction Country Distribution'
                    }
                }
            }
        });
    }
}

/**
 * Get CSRF token from cookies
 */
function getCsrfToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 'csrftoken='.length) === 'csrftoken=') {
                cookieValue = decodeURIComponent(cookie.substring('csrftoken='.length));
                break;
            }
        }
    }
    return cookieValue;
}
