document.addEventListener('DOMContentLoaded', function() {
    // Authentication status check function
    function checkAuthStatus() {
        // Check for auth token in localStorage or sessionStorage
        const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
        
        // If no token is found and user is on a protected page, redirect to login
        if (!token && document.querySelector('meta[name="auth-required"]')) {
            window.location.href = '/login/?next=' + encodeURIComponent(window.location.pathname);
        }
    }
    
    // Run auth check on page load
    checkAuthStatus();

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

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Add animation to progress bars
    const progressBars = document.querySelectorAll('.progress-bar');
    if (progressBars.length > 0) {
        const animateProgressBars = () => {
            progressBars.forEach(bar => {
                const width = bar.getAttribute('aria-valuenow') + '%';
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = width;
                    bar.style.transition = 'width 1s ease-in-out';
                }, 100);
            });
        };

        // Check if element is in viewport
        const isInViewport = (element) => {
            const rect = element.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.right <= (window.innerWidth || document.documentElement.clientWidth)
            );
        };

        // Animate progress bars when they come into view
        let animated = false;
        window.addEventListener('scroll', () => {
            if (!animated && progressBars.length > 0 && isInViewport(progressBars[0])) {
                animateProgressBars();
                animated = true;
            }
        });

        // Initial check
        if (isInViewport(progressBars[0])) {
            animateProgressBars();
            animated = true;
        }
    }

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Add animation to hero section
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
        heroSection.classList.add('animate__animated', 'animate__fadeIn');
    }

    // Highlight active section in navbar based on scroll position
    const sections = document.querySelectorAll('section[id]');
    if (sections.length > 0) {
        window.addEventListener('scroll', () => {
            let current = '';
            sections.forEach(section => {
                const sectionTop = section.offsetTop;
                const sectionHeight = section.clientHeight;
                if (pageYOffset >= sectionTop - 200) {
                    current = section.getAttribute('id');
                }
            });

            document.querySelectorAll('.navbar-nav a').forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + current) {
                    link.classList.add('active');
                }
            });
        });
    }

    // Course search filter functionality
    const searchForm = document.querySelector('form[action*="course-list"]');
    if (searchForm) {
        const searchInput = searchForm.querySelector('input[name="search"]');
        const searchButton = searchForm.querySelector('button[type="submit"]');
        
        // Disable empty searches
        searchForm.addEventListener('submit', function(e) {
            if (searchInput.value.trim() === '') {
                e.preventDefault();
                searchInput.classList.add('is-invalid');
                setTimeout(() => {
                    searchInput.classList.remove('is-invalid');
                }, 3000);
            }
        });

        // Enable search button only when input has content
        searchInput.addEventListener('input', function() {
            if (this.value.trim() !== '') {
                searchButton.disabled = false;
            } else {
                searchButton.disabled = true;
            }
        });

        // Initialize search button state
        if (searchInput.value.trim() === '') {
            searchButton.disabled = true;
        }
    }

    // Animate cards on hover
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px)';
            this.style.boxShadow = '0 15px 30px rgba(0, 0, 0, 0.1)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
        });
    });
}); 