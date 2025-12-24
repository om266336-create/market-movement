document.addEventListener('DOMContentLoaded', () => {
    // Add fade-in class to body when page loads
    document.body.classList.add('fade-in');

    // Handle all link clicks
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a');

        // If it's a link to a local page and not an anchor link or new tab
        if (link &&
            link.href.startsWith(window.location.origin) &&
            !link.href.includes('#') &&
            link.target !== '_blank') {

            e.preventDefault();
            const href = link.href;

            // Add fade-out class
            document.body.classList.remove('fade-in');
            document.body.classList.add('fade-out');

            // Wait for animation to finish before navigating
            setTimeout(() => {
                window.location.href = href;
            }, 500); // Match this with CSS transition duration
        }
    });

    // Handle back/forward cache (bfcache)
    window.addEventListener('pageshow', (event) => {
        if (event.persisted) {
            document.body.classList.remove('fade-out');
            document.body.classList.add('fade-in');
        }
    });
});
