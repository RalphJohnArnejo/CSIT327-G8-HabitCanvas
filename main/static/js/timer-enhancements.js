// Advanced Timer Features Enhancement Script
// This script adds streak tracking, charts, and enhanced analytics to the timer page

(function () {
    'use strict';

    // Wait for DOM and Chart.js to load
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded, charts will not display');
    }

    let currentStreakData = { current: 0, longest: 0 };
    let weeklyChart = null;

    // Add streak badge CSS
    const streakBadgeStyles = `
        .streak-badge-timer {
            margin: 15px 0 0 0;
            max-width: 250px;
            background: linear-gradient(135deg, #ff6b35, #ff8c42);
            color: #fff;
            padding: 8px 16px;
            border-radius: 20px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(255,107,53,0.3);
            font-weight: 700;
            animation: pulseStreak 2s infinite;
            position: absolute;
            right: 30px; 
        }

        @keyframes pulseStreak {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        .streak-badge-timer i { font-size: 18px; }
        .streak-number { font-size: 20px; font-weight: 800; margin: 0 4px; }
    `;

    // Inject styles
    const styleEl = document.createElement('style');
    styleEl.textContent = streakBadgeStyles;
    document.head.appendChild(styleEl);

    // Add streak badge to UI - positioned below mode buttons (Long Break), right-aligned
    function addStreakBadge() {
        const modeButtons = document.querySelector('.mode-buttons');
        if (modeButtons && !document.getElementById('streakBadgeTimer')) {
            // Create wrapper with clearfix
            const wrapper = document.createElement('div');
            wrapper.style.cssText = 'overflow: visible; margin-bottom: 0;';

            const badge = document.createElement('div');
            badge.id = 'streakBadgeTimer';
            badge.className = 'streak-badge-timer';
            badge.innerHTML = '<i class="fa fa-fire"></i><span class="streak-number" id="streakNumberDisplay">0</span> day streak';

            wrapper.appendChild(badge);

            // Insert wrapper after the mode-buttons container
            if (modeButtons.nextSibling) {
                modeButtons.parentNode.insertBefore(wrapper, modeButtons.nextSibling);
            } else {
                modeButtons.parentNode.appendChild(wrapper);
            }
        }
    }

    // Fetch and display enhanced stats
    async function fetchEnhancedStats() {
        try {
            const response = await fetch('/timer/get_stats/');
            const data = await response.json();

            // Update streak badge
            const streakNum = document.getElementById('streakNumberDisplay');
            if (streakNum) {
                streakNum.textContent = data.streak || 0;
            }

            currentStreakData = {
                current: data.streak || 0,
                longest: data.longest_streak || 0
            };

            // Store data for modal
            window.timerStatsData = data;

            console.log('Timer stats loaded:', data);

        } catch (error) {
            console.error('Error fetching timer stats:', error);
        }
    }

    // Enhance stats modal when opened
    function enhanceStatsModal() {
        const statsModal = document.getElementById('statsModal');
        if (!statsModal) return;

        const openStatsBtn = document.getElementById('openStats');
        if (openStatsBtn) {
            openStatsBtn.addEventListener('click', async () => {
                // Fetch latest data
                await fetchEnhancedStats();

                setTimeout(() => {
                    if (window.timerStatsData) {
                        addChartToStatsModal(window.timerStatsData);
                        addEnhancedMetrics(window.timerStatsData);
                    }
                }, 100);
            });
        }
    }

    function addChartToStatsModal(data) {
        if (!window.Chart || !data.daily_stats) return;

        // Find stats cards container
        const statsCards = document.querySelector('.stats-cards');
        if (!statsCards) return;

        // Check if chart already exists
        let chartContainer = document.getElementById('chartContainerEnhanced');
        if (!chartContainer) {
            chartContainer = document.createElement('div');
            chartContainer.id = 'chartContainerEnhanced';
            chartContainer.style.cssText = 'margin: 20px 0; padding: 15px; background: #f3f4f6; border-radius: 8px;';
            chartContainer.innerHTML = '<canvas id="weeklyTrendChartEnhanced"></canvas>';
            statsCards.parentNode.insertBefore(chartContainer, statsCards);
        }

        const canvas = document.getElementById('weeklyTrendChartEnhanced');
        if (!canvas) return;

        // Destroy old chart
        if (weeklyChart) {
            weeklyChart.destroy();
        }

        const ctx = canvas.getContext('2d');
        const labels = data.daily_stats.map(d => {
            const date = new Date(d.date);
            return date.toLocaleDateString('en-US', { weekday: 'short' });
        });
        const minutes = data.daily_stats.map(d => d.minutes || 0);

        weeklyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Focus Minutes',
                    data: minutes,
                    borderColor: '#1f6feb',
                    backgroundColor: 'rgba(31, 111, 235, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4,
                    pointBackgroundColor: '#1f6feb'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    function addEnhancedMetrics(data) {
        // Check if metrics already added
        if (document.getElementById('enhancedMetricsGrid')) return;

        const statsCards = document.querySelector('.stats-cards');
        if (!statsCards) return;

        const metricsGrid = document.createElement('div');
        metricsGrid.id = 'enhancedMetricsGrid';
        metricsGrid.style.cssText = 'display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 15px;';
        metricsGrid.innerHTML = `
            <div style="background: linear-gradient(135deg, #ff6b35, #ff8c42); padding: 15px; border-radius: 8px; color: #fff;">
                <div style="font-size: 12px; font-weight: 600; margin-bottom: 5px; opacity: 0.9;">🔥 CURRENT STREAK</div>
                <div style="font-size: 28px; font-weight: 800;">${data.streak || 0} days</div>
            </div>
            <div style="background: linear-gradient(135deg, #1f6feb, #4a90ff); padding: 15px; border-radius: 8px; color: #fff;">
                <div style="font-size: 12px; font-weight: 600; margin-bottom: 5px; opacity: 0.9;">🏆 BEST STREAK</div>
                <div style="font-size: 28px; font-weight: 800;">${data.longest_streak || 0} days</div>
            </div>
            <div style="background: linear-gradient(135deg, #22c55e, #3dd96d); padding: 15px; border-radius: 8px; color: #fff;">
                <div style="font-size: 12px; font-weight: 600; margin-bottom: 5px; opacity: 0.9;">📊 AVG SESSION</div>
                <div style="font-size: 28px; font-weight: 800;">${data.average_session_minutes || 0} min</div>
            </div>
            <div style="background: linear-gradient(135deg, #8b5cf6, #a78bfa); padding: 15px; border-radius: 8px; color: #fff;">
                <div style="font-size: 12px; font-weight: 600; margin-bottom: 5px; opacity: 0.9;">✅ TOTAL</div>
                <div style="font-size: 28px; font-weight: 800;">${data.total_sessions || 0} sessions</div>
            </div>
        `;

        statsCards.parentNode.insertBefore(metricsGrid, statsCards);
    }

    // Initialize on DOM ready
    function init() {
        addStreakBadge();
        enhanceStatsModal();
        fetchEnhancedStats();

        // Refresh stats every 30 seconds
        setInterval(fetchEnhancedStats, 30000);
    }

    // Wait for page load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
