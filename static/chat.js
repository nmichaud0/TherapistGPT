let user_name = 'user';
let user_name_changed = false;
let valid_api_key = false;
const DEBUG = false;

document.addEventListener('DOMContentLoaded', () => {
    const messageForm = document.getElementById('message-form');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-button');
    const messagesContainer = document.getElementById('messages-container');
    const apiKeyBtn = document.getElementById('api-btn');
    const checkboxGPT = document.getElementById('checkbox-GPT');
    const labelGPT = document.getElementById('GPT-label');
    const fetchDataBtn = document.getElementById('download-data-btn');

    userInput.addEventListener('input', (event) => {
        const textarea = event.target;
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
        //get current height of textarea
        const height = textarea.scrollHeight;
        sendBtn.style.height = height + 'px';

    });


    fetchDataBtn.addEventListener('click', async (event) => {
        const response = await fetch('/therapy/download-data/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
        });
        const data = await response.json();

        // new download with the data as .json file
        const jsonString = JSON.stringify(data);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = 'TherapistGPT-session-data.json';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // Set the checkbox GPT to checked
    checkboxGPT.checked = true;

    checkboxGPT.addEventListener('click', async (event) => {
        let model;
        if (checkboxGPT.checked) {

            model = 'GPT4'

            labelGPT.innerHTML = ' GPT-4    ';
        } else {

            model = 'GPT3.5'

            labelGPT.innerHTML = 'GPT-3.5';
        }

          if (model) {
              const response = await fetch('/therapy/update-model/', {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/x-www-form-urlencoded',
                      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                  },
                  body: new URLSearchParams({ model: model }),
    });
              await response.json();
  }
    });


        messageForm.addEventListener('keydown', (event) => {

            if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            const userMessage = userInput.value.trim();

            if (userMessage) {

                // Get amount of messages in the message-container
                const messages = document.getElementById('messages-container').children;
                const message_count = messages.length;

                if (message_count <= 2 && !DEBUG) {
                alert('This digital therapist is a research experiment, not a medical tool. It\'s not a substitute for ' +
                    'professional mental health care. If you need support, seek help from a qualified professional.' +
                    ' Use at your own discretion.');
                }


                // Display user message
                addMessageToChat('user', userMessage, false);

                // Clear input field
                userInput.value = '';

                // Send user message to TherapistGPT
                sendMessageToTherapist(userMessage).then((message) => {
                    // Display therapist response
                    addMessageToChat('therapist', message, true);
                });
            }
        }});

        async function addMessageToChat(sender, message, withTypingEffect = false) {
            let sender_name;
            const messageElement = document.createElement('div');
            messageElement.classList.add('message', sender);

            if (user_name !== 'user' && user_name_changed) {

                user_name_changed = false;

                const userNamesSpans = document.getElementsByClassName('message-sender');

                for (let i = 0; i < userNamesSpans.length; i++) {
                    if (userNamesSpans[i].textContent === 'User:') {
                        userNamesSpans[i].textContent = user_name + ':';
                    }
                }

            }

            message = message.replace(/\n/g, '<br>')

            if (sender === 'user') {
                sender_name = user_name;
            } else {
                sender_name = sender;
            }

            // capitalize the sender name
            sender_name = sender_name.charAt(0).toUpperCase() + sender_name.slice(1);

            const TherapistLogo = sender === 'Therapist' ? '<img src="/static/img/TherapistGPT_logo.png" alt="logo" class="message-logo">' : '';

            const logoSrc = sender_name === 'Therapist' ? "/static/img/TherapistGPT_logo.png" : "/static/img/UserGPT_logo.png";
            const logoHtml = `<img src="${logoSrc}" alt="logo" class="message-logo">`;

            messageElement.innerHTML = `
        <div class="message-box">
            <div class="message-content">
                ${logoHtml}
                <span class="message-sender">${sender_name}:</span>
                <span class="message-text"></span>
            </div>
        </div>
    `;

            messagesContainer.appendChild(messageElement);

            const messageTextElement = messageElement.querySelector('.message-text');
            if (withTypingEffect && !DEBUG) {
                for (const word of message.split(' ')) {
                    messageTextElement.innerHTML += word + ' ';
                    await new Promise((resolve) => setTimeout(resolve, 75));
                }
            } else {
                messageTextElement.innerHTML = message;
            }

            messagesContainer.scrollTo({
                top: messagesContainer.scrollHeight,
                behavior: 'smooth',
            });

            messageElement.scrollIntoView({behavior: "smooth", block: "end"});

        }

        async function sendMessageToTherapist(message, first_msg=false) {
            // Implement the API call to TherapistGPT (using Fetch or Axios)

            const response = await fetch('/therapy/api-message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                },
                body: new URLSearchParams({input_text: message}),
            });
            const data = await response.json();

            if (data.hasOwnProperty('user_name')) {
                user_name = data.user_name;
                user_name_changed = true;
            }

            if (first_msg) {
                return data.response;
            }
            if (data.response === false) {
                alert('Please provide a valid OpenAI API Key, with the blue button on the bottom right of the window.');
            } else {

                return data.response;}

            // For now, return a dummy response
            // return new Promise((resolve) =>
            //     setTimeout(() => resolve('This is a dummy therapist response.'), 1000)
            // );
        }

        // Send first message to TherapistGPT
        sendMessageToTherapist('Start_conversation', true).then((response) => {
            addMessageToChat('therapist', response, true);
        });

        async function onApiKeyBtnClick() {
            const apiKey = window.prompt('Please enter your OpenAI API key, we will only use it to query ' +
                'OpenAI APIs for the purpose of the digital therapist. No informations are stored outside' +
                ' of therapy sessions:', '');

            if (apiKey) {
              const response = await fetch('/therapy/update-api-key/', {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/x-www-form-urlencoded',
                      'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                  },
                  body: new URLSearchParams({ api_key: apiKey }),
    });
              const api_answer = await response.json();

              console.log(api_answer)

                if (api_answer.response['api_key_valid'] === true) {
                    valid_api_key = true;
                } else {
                    alert('Invalid API key');
                }

                if (api_answer.response['gpt4'] === false) {
                    // if checkboxGPT is checked, uncheck it
                    if (checkboxGPT.checked) {
                        checkboxGPT.click();
                    }

                    alert("You apparently don't have access yet to GPT-4 API, please notice that TherapistGPT have " +
                        "much worse performances running on GPT-3.5.")

                }
  } }

        if (apiKeyBtn) {
            apiKeyBtn.addEventListener('click', onApiKeyBtnClick);
            {
            }
        }

});
