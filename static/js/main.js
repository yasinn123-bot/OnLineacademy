document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Video player functionality
    const videoPlayers = document.querySelectorAll('.video-player');
    if (videoPlayers.length > 0) {
        videoPlayers.forEach(player => {
            const videoId = player.getAttribute('data-video-id');
            const playerElement = player.querySelector('.player');
            
            if (videoId && playerElement) {
                // Implement video player logic here
                console.log(`Video player initialized for video ID: ${videoId}`);
            }
        });
    }

    // Course progress tracking
    const progressBars = document.querySelectorAll('.course-progress');
    if (progressBars.length > 0) {
        progressBars.forEach(bar => {
            const completed = parseInt(bar.getAttribute('data-completed') || 0);
            const total = parseInt(bar.getAttribute('data-total') || 0);
            
            if (total > 0) {
                const percentage = Math.round((completed / total) * 100);
                bar.style.width = `${percentage}%`;
                bar.setAttribute('aria-valuenow', percentage);
                bar.textContent = `${percentage}%`;
            }
        });
    }

    // JWT Token Management
    const getAccessToken = () => {
        return localStorage.getItem('accessToken');
    };

    const getRefreshToken = () => {
        return localStorage.getItem('refreshToken');
    };

    const setTokens = (accessToken, refreshToken) => {
        localStorage.setItem('accessToken', accessToken);
        localStorage.setItem('refreshToken', refreshToken);
    };

    const clearTokens = () => {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
    };

    // Refresh token function
    const refreshToken = async () => {
        try {
            const refreshToken = getRefreshToken();
            if (!refreshToken) {
                throw new Error('No refresh token available');
            }

            const response = await fetch('/api/token/refresh/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh: refreshToken }),
            });

            if (!response.ok) {
                throw new Error('Failed to refresh token');
            }

            const data = await response.json();
            setTokens(data.access, refreshToken);
            return data.access;
        } catch (error) {
            console.error('Error refreshing token:', error);
            clearTokens();
            window.location.href = '/login';
            throw error;
        }
    };

    // API Request with token refresh capability
    const apiRequest = async (url, options = {}) => {
        const defaultHeaders = {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        };

        // Add Authorization header if access token exists
        const accessToken = getAccessToken();
        if (accessToken) {
            defaultHeaders['Authorization'] = `Bearer ${accessToken}`;
        }

        // Merge default headers with provided options
        const requestOptions = {
            ...options,
            headers: {
                ...defaultHeaders,
                ...options.headers,
            },
            credentials: 'same-origin',
        };

        try {
            let response = await fetch(url, requestOptions);

            // If response is 401 (Unauthorized), try to refresh the token
            if (response.status === 401) {
                try {
                    const newAccessToken = await refreshToken();
                    
                    // Update Authorization header with new token
                    requestOptions.headers['Authorization'] = `Bearer ${newAccessToken}`;
                    
                    // Retry request with new token
                    response = await fetch(url, requestOptions);
                } catch (refreshError) {
                    console.error('Token refresh failed:', refreshError);
                    throw refreshError;
                }
            }

            if (!response.ok) {
                throw new Error(`API request failed with status ${response.status}`);
            }

            return response.json();
        } catch (error) {
            console.error(`Error during API request to ${url}:`, error);
            throw error;
        }
    };

    // Material completion marking
    const completionButtons = document.querySelectorAll('.mark-completed-btn');
    if (completionButtons.length > 0) {
        completionButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const materialId = this.getAttribute('data-material-id');
                
                if (materialId) {
                    apiRequest(`/api/materials/${materialId}/mark_completed/`, {
                        method: 'POST',
                        body: JSON.stringify({}),
                    })
                    .then(data => {
                        if (data.detail) {
                            this.innerHTML = '<i class="fas fa-check-circle"></i> Выполнено';
                            this.classList.remove('btn-primary');
                            this.classList.add('btn-success');
                            this.disabled = true;
                        }
                    })
                    .catch(error => {
                        console.error('Error marking material as completed:', error);
                    });
                }
            });
        });
    }

    // Helper function to get CSRF cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Login form handling
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const formDataObj = {};
            formData.forEach((value, key) => {
                formDataObj[key] = value;
            });
            
            fetch('/api/token/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(formDataObj),
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Login failed');
                }
                return response.json();
            })
            .then(data => {
                // Store tokens
                setTokens(data.access, data.refresh);
                
                // Redirect to dashboard or home page
                window.location.href = '/dashboard/';
            })
            .catch(error => {
                console.error('Error during login:', error);
                // Show error message
                const errorElement = document.getElementById('login-error');
                if (errorElement) {
                    errorElement.textContent = 'Неверное имя пользователя или пароль';
                    errorElement.classList.remove('d-none');
                }
            });
        });
    }

    // Logout handling
    const logoutButton = document.getElementById('logout-button');
    if (logoutButton) {
        logoutButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            const refreshToken = getRefreshToken();
            
            fetch('/api/token/logout/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Authorization': `Bearer ${getAccessToken()}`
                },
                body: JSON.stringify({ refresh: refreshToken }),
                credentials: 'same-origin'
            })
            .then(() => {
                // Clear tokens from local storage
                clearTokens();
                
                // Redirect to login page
                window.location.href = '/';
            })
            .catch(error => {
                console.error('Error during logout:', error);
                // Clear tokens anyway and redirect
                clearTokens();
                window.location.href = '/';
            });
        });
    }

    // Comment form handling
    const commentForm = document.getElementById('comment-form');
    if (commentForm) {
        commentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const materialId = formData.get('material');
            
            apiRequest('/api/comments/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData,
            })
            .then(data => {
                // Refresh comments or add the new comment to the DOM
                window.location.reload();
            })
            .catch(error => {
                console.error('Error submitting comment:', error);
            });
        });
    }

    // Test submission
    const testForm = document.getElementById('test-form');
    if (testForm) {
        testForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const testId = this.getAttribute('data-test-id');
            const answers = [];
            
            // Collect all selected answers
            const questions = document.querySelectorAll('.question');
            questions.forEach(question => {
                const questionId = question.getAttribute('data-question-id');
                const selectedAnswer = question.querySelector('input[type="radio"]:checked');
                
                if (selectedAnswer) {
                    answers.push({
                        question_id: questionId,
                        answer_id: selectedAnswer.value
                    });
                }
            });
            
            if (answers.length !== questions.length) {
                alert('Пожалуйста, ответьте на все вопросы');
                return;
            }
            
            apiRequest(`/api/tests/${testId}/submit/`, {
                method: 'POST',
                body: JSON.stringify({ answers }),
            })
            .then(data => {
                if (data.certificate_id) {
                    window.location.href = `/certificates/${data.certificate_id}/`;
                } else {
                    const resultElement = document.getElementById('test-result');
                    if (resultElement) {
                        resultElement.innerHTML = `
                            <div class="alert ${data.passed ? 'alert-success' : 'alert-danger'}">
                                <h4>${data.passed ? 'Поздравляем!' : 'Попробуйте еще раз'}</h4>
                                <p>Ваш результат: ${data.score.toFixed(1)}%</p>
                                <p>${data.passed ? 'Вы успешно прошли тест!' : 'К сожалению, вы не прошли тест. Попробуйте снова после повторения материала.'}</p>
                            </div>
                        `;
                        resultElement.scrollIntoView({ behavior: 'smooth' });
                    }
                }
            })
            .catch(error => {
                console.error('Error submitting test:', error);
            });
        });
    }

    // Check if user is logged in on page load
    const checkAuthStatus = () => {
        const accessToken = getAccessToken();
        
        if (accessToken) {
            // Verify token is valid
            fetch('/api/token/verify/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token: accessToken }),
            })
            .then(response => {
                if (!response.ok) {
                    // Try to refresh token
                    return refreshToken().catch(() => {
                        throw new Error('Authentication required');
                    });
                }
                return true;
            })
            .catch(error => {
                console.error('Auth check failed:', error);
                
                // Don't redirect on home or login pages
                const path = window.location.pathname;
                if (path !== '/' && !path.includes('/login') && !path.includes('/register')) {
                    window.location.href = '/';
                }
            });
        } else {
            // If no token found, don't redirect from protected pages
            // User might be authenticated through Django sessions
            // Removing the redirection code entirely
        }
    };

    // Run auth check on page load
    checkAuthStatus();
}); 