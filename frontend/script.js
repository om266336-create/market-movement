// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById("analysis-form");
    const analyzeBtn = document.getElementById("analyze-btn");
    const textInput = document.getElementById("text-input");
    const resultsSection = document.getElementById("results-section");
    const charCount = document.getElementById("char-count");

    let analysisData = null;

    // ==================== THEME TOGGLE ====================
    const themeToggle = document.getElementById("theme-toggle");
    const body = document.body;

    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    body.className = savedTheme + '-theme';

    themeToggle.addEventListener('click', () => {
        const isDark = body.classList.contains('dark-theme');
        body.className = isDark ? 'light-theme' : 'dark-theme';
        localStorage.setItem('theme', isDark ? 'light' : 'dark');
    });

    // ==================== CHARACTER COUNT ====================
    textInput.addEventListener('input', () => {
        const count = textInput.value.length;
        charCount.textContent = count;
        charCount.style.color = count > 512 ? 'var(--danger)' : 'var(--text-muted)';
    });

    // ==================== SENTIMENT ANALYSIS ====================
    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        const text = textInput.value;
        if (!text.trim()) return;

        // Show loading state
        analyzeBtn.disabled = true;
        analyzeBtn.classList.add('loading');

        try {
            const response = await fetch("/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text })
            });

            analysisData = await response.json();

            // Show results
            resultsSection.style.display = 'block';

            // Update sentiment metrics
            document.getElementById("sentiment").textContent = analysisData.sentiment;
            document.getElementById("confidence").textContent = analysisData.confidence + '%';
            document.getElementById("confidence-level").textContent = analysisData.confidenceLevel.level;
            document.getElementById("confidence-level").style.color = analysisData.confidenceLevel.color;
            document.getElementById("prediction").textContent = analysisData.prediction;

            // Impact score
            document.getElementById("impact-score").textContent =
                (analysisData.impact.score > 0 ? '+' : '') + analysisData.impact.score;
            document.getElementById("impact-level").textContent = analysisData.impact.level;

            // Update gauge
            updateGauge(analysisData.impact.score);

            // AI Insight
            document.getElementById("ai-insight").textContent = analysisData.insight;

            // Trend badge
            const trendBadge = document.getElementById("trend-badge");
            if (analysisData.trend) {
                trendBadge.textContent = `${analysisData.trend.emoji} ${analysisData.trend.trend}: ${analysisData.trend.previous} → ${analysisData.trend.current}`;
                trendBadge.className = 'trend-badge ' + analysisData.trend.trend.toLowerCase();
                trendBadge.style.display = 'block';
            } else {
                trendBadge.style.display = 'none';
            }

            // Stock data
            const stockInfo = document.getElementById("stock-info");
            if (analysisData.stock) {
                document.getElementById("stock-symbol").textContent = analysisData.stock.symbol;
                document.getElementById("stock-name").textContent = analysisData.stock.name;
                document.getElementById("stock-price").textContent = `$${analysisData.stock.price.toFixed(2)}`;

                const changeEl = document.getElementById("stock-change");
                const isPositive = analysisData.stock.change >= 0;
                changeEl.textContent = `${isPositive ? '+' : ''}${analysisData.stock.change.toFixed(2)} (${isPositive ? '+' : ''}${analysisData.stock.changePercent.toFixed(2)}%)`;
                changeEl.className = `change-badge ${isPositive ? 'positive' : 'negative'}`;

                stockInfo.style.display = 'block';
            } else {
                stockInfo.style.display = 'none';
            }

            // Scroll to results
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

        } catch (error) {
            console.error('Error:', error);
            alert('Error analyzing sentiment. Please check if the server is running.');
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.classList.remove('loading');
        }
    });

    // ==================== GAUGE UPDATE ====================
    function updateGauge(score) {
        const marker = document.getElementById('gauge-marker');
        const percentage = ((score + 100) / 200) * 100;
        marker.style.left = percentage + '%';
    }

    // ==================== EXPORT PDF ====================
    const exportPdfBtn = document.getElementById('export-pdf');
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', async () => {
            if (!analysisData) {
                alert('Please analyze some text first!');
                return;
            }

            // Using native PDF generation (simple approach)
            const printContent = `
                AI Market Intelligence Report
                ============================
                Date: ${new Date().toLocaleDateString()}
                
                SENTIMENT ANALYSIS
                ------------------
                Sentiment: ${analysisData.sentiment}
                Confidence: ${analysisData.confidence}% (${analysisData.confidenceLevel.level})
                Prediction: ${analysisData.prediction}
                Impact Score: ${analysisData.impact.score > 0 ? '+' : ''}${analysisData.impact.score} (${analysisData.impact.level})
                
                AI INSIGHT
                ----------
                ${analysisData.insight}
                
                ${analysisData.stock ? `
                STOCK DATA
                ----------
                Symbol: ${analysisData.stock.symbol}
                Price: $${analysisData.stock.price}
                Change: ${analysisData.stock.change > 0 ? '+' : ''}${analysisData.stock.change} (${analysisData.stock.changePercent.toFixed(2)}%)
                ` : ''}
                
                ---
                Generated by AI Market Intelligence
                This is for educational purposes only. Not financial advice.
            `;

            const win = window.open('', '', 'width=600,height=400');
            win.document.write('<pre style="font-family: monospace; padding: 20px;">' + printContent + '</pre>');
            win.document.close();
            win.print();
        });
    }
});
