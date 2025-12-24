// ==================== DASHBOARD INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function () {
    // ==================== THEME TOGGLE ====================
    const themeToggle = document.getElementById("theme-toggle");
    const body = document.body;

    const savedTheme = localStorage.getItem('theme') || 'dark';
    body.className = savedTheme + '-theme';

    themeToggle.addEventListener('click', () => {
        const isDark = body.classList.contains('dark-theme');
        body.className = isDark ? 'light-theme' : 'dark-theme';
        localStorage.setItem('theme', isDark ? 'light' : 'dark');
    });

    // ==================== VARIABLES ====================
    let stockChart = null;
    let currentSymbol = null;
    let currentPeriod = '1mo';

    // ==================== STOCK SEARCH ====================
    const searchInput = document.getElementById('stock-search');
    const searchBtn = document.getElementById('search-btn');
    const symbolChips = document.querySelectorAll('.symbol-chip');

    searchBtn.addEventListener('click', () => {
        const symbol = searchInput.value.trim().toUpperCase();
        if (symbol) {
            loadStockData(symbol);
        }
    });

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const symbol = searchInput.value.trim().toUpperCase();
            if (symbol) {
                loadStockData(symbol);
            }
        }
    });

    symbolChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const symbol = chip.dataset.symbol;
            searchInput.value = symbol;
            loadStockData(symbol);
        });
    });

    // ==================== LOAD STOCK DATA ====================
    async function loadStockData(symbol) {
        currentSymbol = symbol;

        try {
            const response = await fetch(`/stock/${symbol}?period=${currentPeriod}`);
            const data = await response.json();

            if (data.error) {
                alert('Error: ' + data.error);
                return;
            }

            // Update header
            document.getElementById('current-symbol').textContent = data.symbol;
            document.getElementById('current-name').textContent = data.name;

            // Update price
            document.getElementById('stock-price').textContent = `$${data.price.toFixed(2)}`;

            const changeEl = document.getElementById('stock-change');
            const isPositive = data.change >= 0;
            changeEl.textContent = `${isPositive ? '+' : ''}${data.change.toFixed(2)} (${isPositive ? '+' : ''}${data.changePercent.toFixed(2)}%)`;
            changeEl.className = `change-badge ${isPositive ? 'positive' : 'negative'}`;

            // Update chart
            updateStockChart(data.dates, data.prices, data.symbol);

            // Load technical indicators
            loadTechnicalIndicators(symbol, data);

            // Update probability (simulated based on sentiment)
            updateProbability(data);

            // Update data freshness
            document.getElementById('data-freshness').textContent = new Date().toLocaleTimeString();

        } catch (error) {
            console.error('Error loading stock data:', error);
            alert('Error loading stock data. Please check if the server is running.');
        }
    }

    // ==================== STOCK CHART ====================
    function updateStockChart(dates, prices, symbol) {
        const ctx = document.getElementById('stock-chart').getContext('2d');

        if (stockChart) {
            stockChart.destroy();
        }

        const isPositive = prices[prices.length - 1] >= prices[0];
        const lineColor = isPositive ? 'rgba(0, 212, 138, 1)' : 'rgba(255, 82, 82, 1)';
        const bgGradient = ctx.createLinearGradient(0, 0, 0, 200);
        bgGradient.addColorStop(0, isPositive ? 'rgba(0, 212, 138, 0.3)' : 'rgba(255, 82, 82, 0.3)');
        bgGradient.addColorStop(1, 'rgba(0, 0, 0, 0)');

        stockChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: `${symbol} Price`,
                    data: prices,
                    borderColor: lineColor,
                    backgroundColor: bgGradient,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: lineColor
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(18, 18, 26, 0.95)',
                        titleColor: '#fff',
                        bodyColor: '#a0a0b0',
                        borderColor: 'rgba(102, 126, 234, 0.3)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: (context) => `$${context.parsed.y.toFixed(2)}`
                        }
                    }
                },
                scales: {
                    y: {
                        ticks: {
                            color: '#8a8a9a',
                            callback: (value) => '$' + value.toFixed(0)
                        },
                        grid: { color: 'rgba(255,255,255,0.03)' }
                    },
                    x: {
                        ticks: {
                            color: '#8a8a9a',
                            maxTicksLimit: 6
                        },
                        grid: { display: false }
                    }
                },
                animation: {
                    duration: 1500,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    // ==================== TECHNICAL INDICATORS ====================
    function loadTechnicalIndicators(symbol, data) {
        // Calculate RSI (simplified calculation)
        const prices = data.prices;
        const rsi = calculateRSI(prices, 14);

        document.getElementById('rsi-value').textContent = rsi.toFixed(1);
        document.getElementById('rsi-marker').style.left = rsi + '%';

        const rsiSignal = document.getElementById('rsi-signal');
        if (rsi > 70) {
            rsiSignal.textContent = 'Overbought';
            rsiSignal.className = 'indicator-signal bearish';
        } else if (rsi < 30) {
            rsiSignal.textContent = 'Oversold';
            rsiSignal.className = 'indicator-signal bullish';
        } else {
            rsiSignal.textContent = 'Neutral';
            rsiSignal.className = 'indicator-signal neutral';
        }

        // Calculate MACD (simplified)
        const macd = calculateMACD(prices);
        document.getElementById('macd-value').textContent = macd.macd.toFixed(2);
        document.getElementById('macd-signal-value').textContent = macd.signal.toFixed(2);
        document.getElementById('macd-histogram').textContent = macd.histogram.toFixed(2);

        const macdSignal = document.getElementById('macd-signal');
        if (macd.histogram > 0) {
            macdSignal.textContent = 'Bullish';
            macdSignal.className = 'indicator-signal bullish';
        } else {
            macdSignal.textContent = 'Bearish';
            macdSignal.className = 'indicator-signal bearish';
        }

        // Calculate Moving Averages
        const currentPrice = prices[prices.length - 1];
        const ma20 = calculateMA(prices, 20);
        const ma50 = calculateMA(prices, Math.min(50, prices.length));
        const ma200 = calculateMA(prices, Math.min(200, prices.length));

        document.getElementById('ma20-value').textContent = '$' + ma20.toFixed(2);
        document.getElementById('ma50-value').textContent = '$' + ma50.toFixed(2);
        document.getElementById('ma200-value').textContent = '$' + ma200.toFixed(2);

        updateMASignal('ma20-signal', currentPrice, ma20);
        updateMASignal('ma50-signal', currentPrice, ma50);
        updateMASignal('ma200-signal', currentPrice, ma200);
    }

    function calculateRSI(prices, period) {
        if (prices.length < period + 1) return 50;

        let gains = 0;
        let losses = 0;

        for (let i = prices.length - period; i < prices.length; i++) {
            const change = prices[i] - prices[i - 1];
            if (change > 0) {
                gains += change;
            } else {
                losses -= change;
            }
        }

        const avgGain = gains / period;
        const avgLoss = losses / period;

        if (avgLoss === 0) return 100;

        const rs = avgGain / avgLoss;
        return 100 - (100 / (1 + rs));
    }

    function calculateMACD(prices) {
        const ema12 = calculateEMA(prices, 12);
        const ema26 = calculateEMA(prices, 26);
        const macd = ema12 - ema26;

        // Signal line (9-period EMA of MACD) - simplified
        const signal = macd * 0.9;
        const histogram = macd - signal;

        return { macd, signal, histogram };
    }

    function calculateEMA(prices, period) {
        if (prices.length < period) return prices[prices.length - 1];

        const multiplier = 2 / (period + 1);
        let ema = prices.slice(0, period).reduce((a, b) => a + b, 0) / period;

        for (let i = period; i < prices.length; i++) {
            ema = (prices[i] * multiplier) + (ema * (1 - multiplier));
        }

        return ema;
    }

    function calculateMA(prices, period) {
        if (prices.length < period) return prices[prices.length - 1];
        const slice = prices.slice(-period);
        return slice.reduce((a, b) => a + b, 0) / slice.length;
    }

    function updateMASignal(elementId, currentPrice, ma) {
        const element = document.getElementById(elementId);
        if (currentPrice > ma) {
            element.textContent = '↑ Above';
            element.className = 'ma-signal above';
        } else {
            element.textContent = '↓ Below';
            element.className = 'ma-signal below';
        }
    }

    // ==================== PROBABILITY ====================
    function updateProbability(data) {
        const prices = data.prices;
        const trend = prices[prices.length - 1] - prices[0];
        const trendPercent = (trend / prices[0]) * 100;

        // Calculate probabilities based on trend and momentum
        let bullish, bearish, neutral;

        if (trendPercent > 3) {
            bullish = 50 + Math.min(trendPercent * 2, 30);
            bearish = 15;
            neutral = 100 - bullish - bearish;
        } else if (trendPercent < -3) {
            bearish = 50 + Math.min(Math.abs(trendPercent) * 2, 30);
            bullish = 15;
            neutral = 100 - bullish - bearish;
        } else {
            neutral = 50;
            bullish = 25;
            bearish = 25;
        }

        // Update bars
        document.getElementById('prob-bullish').style.width = bullish + '%';
        document.getElementById('prob-neutral').style.width = neutral + '%';
        document.getElementById('prob-bearish').style.width = bearish + '%';

        document.getElementById('prob-bullish-value').textContent = Math.round(bullish) + '%';
        document.getElementById('prob-neutral-value').textContent = Math.round(neutral) + '%';
        document.getElementById('prob-bearish-value').textContent = Math.round(bearish) + '%';

        // Update outlook
        document.getElementById('outlook-short').textContent = bullish > bearish ? '📈 Bullish' : bearish > bullish ? '📉 Bearish' : '➡️ Neutral';
        document.getElementById('outlook-mid').textContent = trendPercent > 0 ? '📈 Bullish' : trendPercent < 0 ? '📉 Bearish' : '➡️ Neutral';

        // Update confidence explanation
        document.getElementById('confidence-explanation').textContent =
            `Based on ${data.dates.length} data points, the stock shows a ${trendPercent > 0 ? 'positive' : 'negative'} trend of ${Math.abs(trendPercent).toFixed(1)}%. ` +
            `Technical indicators suggest ${bullish > bearish ? 'bullish' : 'bearish'} momentum with RSI in ${document.getElementById('rsi-signal').textContent.toLowerCase()} territory.`;
    }

    // ==================== PERIOD BUTTONS ====================
    document.querySelectorAll('.period-btn').forEach(btn => {
        btn.addEventListener('click', async function () {
            if (!currentSymbol) return;

            document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            currentPeriod = this.dataset.period;

            loadStockData(currentSymbol);
        });
    });

    // ==================== SOURCE TABS ====================
    document.querySelectorAll('.source-tab').forEach(tab => {
        tab.addEventListener('click', function () {
            document.querySelectorAll('.source-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.source-panel').forEach(p => p.classList.remove('active'));

            this.classList.add('active');
            document.getElementById('source-' + this.dataset.source).classList.add('active');
        });
    });

    // ==================== COMPARISON ====================
    const addComparisonBtn = document.getElementById('add-comparison');
    const comparisonContainer = document.getElementById('comparison-container');
    let comparisonStocks = [];

    addComparisonBtn.addEventListener('click', () => {
        const symbol = prompt('Enter stock symbol to compare:');
        if (symbol && !comparisonStocks.includes(symbol.toUpperCase())) {
            addComparisonStock(symbol.toUpperCase());
        }
    });

    async function addComparisonStock(symbol) {
        try {
            const response = await fetch(`/stock/${symbol}?period=1mo`);
            const data = await response.json();

            if (data.error) {
                alert('Stock not found: ' + symbol);
                return;
            }

            comparisonStocks.push(symbol);

            // Clear empty state
            const empty = comparisonContainer.querySelector('.comparison-empty');
            if (empty) empty.remove();

            // Create comparison card
            const card = document.createElement('div');
            card.className = 'panel';
            card.innerHTML = `
                <div class="panel-header">
                    <h3>${data.symbol}</h3>
                    <button class="remove-btn" data-symbol="${symbol}">×</button>
                </div>
                <div class="price-display" style="margin-bottom: 0;">
                    <span class="stock-price" style="font-size: 1.5rem;">$${data.price.toFixed(2)}</span>
                    <span class="change-badge ${data.change >= 0 ? 'positive' : 'negative'}">
                        ${data.change >= 0 ? '+' : ''}${data.changePercent.toFixed(2)}%
                    </span>
                </div>
                <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 8px;">${data.name}</p>
            `;

            card.querySelector('.remove-btn').addEventListener('click', () => {
                comparisonStocks = comparisonStocks.filter(s => s !== symbol);
                card.remove();
                if (comparisonStocks.length === 0) {
                    comparisonContainer.innerHTML = '<div class="comparison-empty"><p>Add stocks above to compare</p></div>';
                }
            });

            comparisonContainer.appendChild(card);

        } catch (error) {
            console.error('Error adding comparison:', error);
        }
    }

    // ==================== EXPORT ====================
    document.getElementById('export-pdf')?.addEventListener('click', () => {
        alert('PDF export coming soon! Use browser print for now.');
    });

    document.getElementById('export-csv')?.addEventListener('click', () => {
        if (!currentSymbol) {
            alert('Please select a stock first!');
            return;
        }

        const csv = `Symbol,Price,RSI,MACD
${currentSymbol},$${document.getElementById('stock-price').textContent},${document.getElementById('rsi-value').textContent},${document.getElementById('macd-value').textContent}`;

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentSymbol}-analysis.csv`;
        a.click();
    });
});
