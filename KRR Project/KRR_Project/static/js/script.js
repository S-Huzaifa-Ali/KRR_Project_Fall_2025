document.addEventListener('DOMContentLoaded', function() {
    const chatArea = document.getElementById('chat-area');
    const userInput = document.getElementById('user-input');

    userInput.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    window.sendMessage = async function() {
        const text = userInput.value.trim();
        if (!text) return;

        appendMessage(text, 'user');
        userInput.value = '';
        
        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot loading';
        loadingDiv.id = loadingId;
        loadingDiv.textContent = 'Analyzing emotions...';
        chatArea.appendChild(loadingDiv);
        chatArea.scrollTop = chatArea.scrollHeight;

        try {
            const formData = new FormData();
            formData.append('message', text);

            const response = await fetch('/api/chat/', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();

            if (data.error) {
                appendMessage("Sorry, I encountered an error: " + data.error, 'bot');
            } else {
                let reply = `I detected that you are feeling <strong>${data.emotion}</strong>.<br>Here are some recommendations:`;
                
                if (data.movies.length === 0) {
                    reply += "<br>Sorry, I couldn't find any movies for that emotion.";
                } else {
                    data.movies.forEach(movie => {
                        reply += `
                            <div class="recommendation-card">
                                <h4>${movie.title} (${movie.year})</h4>
                                <p><strong>Director:</strong> ${movie.director}</p>
                                <p><strong>Genre:</strong> ${movie.genre}</p>
                                <p><em>"${movie.review_snippet}"</em></p>
                            </div>
                        `;
                    });
                }

                appendMessage(reply, 'bot', true);
            }

        } catch (error) {
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();
            appendMessage("Sorry, something went wrong with the server.", 'bot');
            console.error(error);
        }
    }

    function appendMessage(text, sender, isHtml = false) {
        const div = document.createElement('div');
        div.className = `message ${sender}`;
        if (isHtml) {
            div.innerHTML = text;
        } else {
            div.textContent = text;
        }
        chatArea.appendChild(div);
        chatArea.scrollTop = chatArea.scrollHeight;
    }
});
