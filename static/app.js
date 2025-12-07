document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("hashtag-form");
    const input = document.getElementById("hashtag-input");
    const resultsDiv = document.getElementById("results");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const hashtag = input.value.trim();
        if (!hashtag) return;

        resultsDiv.innerHTML = "<p>Loading...</p>";

        try {
            const response = await fetch("/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ hashtag })
            });

            const data = await response.json();

            if (response.ok) {
                renderResults(data);
            } else {
                resultsDiv.innerHTML = `<div class="error">${data.error}</div>`;
            }
        } catch (err) {
            resultsDiv.innerHTML = `<div class="error">Request failed: ${err}</div>`;
        }
    });

    function renderResults(data) {
        resultsDiv.innerHTML = "";
        data.posts.forEach(post => {
            const div = document.createElement("div");
            div.className = `post-card ${post.risk_level}`;
            div.innerHTML = `
                <div class="post-header">
                    <span class="rank">#${post.rank}</span>
                    <span class="risk-badge ${post.risk_level}">${post.risk_level.toUpperCase()}</span>
                </div>
                <h4><a href="${post.url}" target="_blank">${post.title}</a></h4>
                <div class="post-meta">${post.subreddit} | ${post.date}</div>
                <div class="snippet">${post.snippet}</div>
                <div class="keywords">Keywords: ${post.keywords.join(", ")}</div>
                <div class="score">Misinfo: ${post.misinfo_score}%, Clickbait: ${post.clickbait_score}</div>
            `;
            resultsDiv.appendChild(div);
        });
    }
});
