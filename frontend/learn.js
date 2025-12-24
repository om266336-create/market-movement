// ==================== LEARN PAGE INITIALIZATION ====================
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

    // ==================== TOPIC NAVIGATION ====================
    const topicLinks = document.querySelectorAll('.topic-link');
    const articles = document.querySelectorAll('.learn-article');

    // Highlight active topic based on scroll position
    function updateActiveLink() {
        let currentActive = null;

        articles.forEach(article => {
            const rect = article.getBoundingClientRect();
            if (rect.top <= 150 && rect.bottom > 150) {
                currentActive = article.id;
            }
        });

        if (currentActive) {
            topicLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + currentActive) {
                    link.classList.add('active');
                }
            });
        }
    }

    window.addEventListener('scroll', updateActiveLink);

    // Smooth scroll to articles
    topicLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetArticle = document.getElementById(targetId);

            if (targetArticle) {
                targetArticle.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });

                // Update active state
                topicLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            }
        });
    });

    // ==================== READING PROGRESS ====================
    // Add a reading progress indicator
    const progressBar = document.createElement('div');
    progressBar.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        z-index: 9999;
        transition: width 0.1s ease;
    `;
    document.body.appendChild(progressBar);

    window.addEventListener('scroll', () => {
        const scrollTop = window.scrollY;
        const docHeight = document.body.scrollHeight - window.innerHeight;
        const progress = (scrollTop / docHeight) * 100;
        progressBar.style.width = progress + '%';
    });

    // ==================== ARTICLE ANIMATIONS ====================
    // Animate articles when they come into view
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const articleObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    articles.forEach(article => {
        article.style.opacity = '0';
        article.style.transform = 'translateY(20px)';
        article.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        articleObserver.observe(article);
    });

    // Make first article visible immediately
    if (articles[0]) {
        articles[0].style.opacity = '1';
        articles[0].style.transform = 'translateY(0)';
    }
});
