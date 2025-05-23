let pendingAction = null; // To store whether user clicked "add" or "remove"
let otpSent = false;
let countdownInterval = null;
let otpExpiryTime = null;
let sessionUser = ""; // Holds the email from backend

document.addEventListener("DOMContentLoaded", function () {
    const path = window.location.pathname;

    if (path === "/dashboard") {
        fetch("/get_current_user")
            .then(res => res.json())
            .then(data => {
                if (data.logged_in) {
                    sessionUser = data.username;
                    const emailInput = document.getElementById("verify_username");
                    if (emailInput) {
                        emailInput.value = sessionUser;
                    }
                } else {
                    console.warn("User not logged in.");
                    window.location.href = "/";
                }
            });
    }
    function showLoader() {
        let loader = document.createElement("div");
        loader.classList.add("loader");
        loader.innerHTML = "Processing...";
        document.body.appendChild(loader);
    }

    function removeLoader() {
        let loader = document.querySelector(".loader");
        if (loader) loader.remove();
    }

    function showAlert(message, type = "info") {
        let alertBox = document.createElement("div");
        alertBox.classList.add("alert", type);
        alertBox.innerText = message;
        document.body.appendChild(alertBox);

        setTimeout(() => {
            alertBox.remove();
        }, 3000);
    }

    function startOTPTimer(durationInSeconds = 120) {
        otpExpiryTime = Date.now() + durationInSeconds * 1000;

        document.getElementById("otp-timer").style.display = "block";

        countdownInterval = setInterval(() => {
            const remaining = Math.floor((otpExpiryTime - Date.now()) / 1000);

            if (remaining <= 0) {
                clearInterval(countdownInterval);
                document.getElementById("otp-countdown").innerText = "Expired";
                showAlert("OTP expired. Please request a new one.", "error");
            } else {
                const minutes = String(Math.floor(remaining / 60)).padStart(2, '0');
                const seconds = String(remaining % 60).padStart(2, '0');
                document.getElementById("otp-countdown").innerText = `${minutes}:${seconds}`;
            }
        }, 1000);
    }

    async function apiRequest(url, method, body = {}) {
        showLoader();
        try {
            const response = await fetch(url, {
                method: method,
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body),
            });
            const data = await response.json();
            removeLoader();
            return data;
        } catch (error) {
            removeLoader();
            showAlert("Network error! Please try again.", "error");
            console.error("API Error:", error);
        }
    }

    window.login = async function () {
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();

        if (!username || !password) {
            showAlert("Please enter email and password!", "error");
            return;
        }

        const data = await apiRequest("/login", "POST", { username, password });

        if (data?.success) {
            sessionStorage.setItem("username", username);
            sessionStorage.setItem("password", password);
            showAlert(data.message, "success");
            setTimeout(() => window.location.href = "/dashboard", 1000);
        } else {
            showAlert(data.message, "error");
        }
    };

    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    window.register = async function () {
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();

        if (!username || !password) {
            showAlert("Please enter email and password!", "error");
            return;
        }

        if (!isValidEmail(username)) {
            showAlert("Please enter a valid email address to register.", "error");
            return;
        }

        const data = await apiRequest("/register", "POST", { username, password });
        showAlert(data?.message || "Registration failed!", data?.success ? "success" : "error");
    };

    function runAddService(password, otp) {
        const serviceName = document.getElementById("service_name").value.trim();
        const serviceIp = document.getElementById("service_ip").value.trim();
        const servicePort = document.getElementById("service_port").value.trim();

        if (!serviceName || !serviceIp || !servicePort) {
            showAlert("All fields are required!", "error");
            return;
        }

        apiRequest("/add_service", "POST", {
            service_name: serviceName,
            service_ip: serviceIp,
            service_port: servicePort,
            password,
            otp
        }).then(data => {
            showAlert(data?.message || "Failed to add service", data?.success ? "success" : "error");
        });
    }

    function runRemoveService(password, otp) {
        const serviceName = document.getElementById("remove_service_name").value.trim();

        if (!serviceName) {
            showAlert("Service name is required!", "error");
            return;
        }

        apiRequest("/remove_service", "POST", {
            service_name: serviceName,
            password,
            otp
        }).then(data => {
            showAlert(data?.message || "Failed to remove service", data?.success ? "success" : "error");
        });
    }

    window.logout = function () {
        sessionStorage.clear();
        window.location.href = "/logout";
    };

    window.showVerificationModal = function (actionType) {
        pendingAction = actionType;
        otpSent = false;
        document.getElementById("verify_otp").style.display = "none";
        document.getElementById("verify_otp").value = "";
        document.getElementById("verifyBtn").innerText = "Confirm";
        document.getElementById("authModal").style.display = "flex";

        // Refill email field from session
        const emailInput = document.getElementById("verify_username");
        if (emailInput && sessionUser) {
            emailInput.value = sessionUser;
        }
    };

    window.closeModal = function () {
        document.getElementById("authModal").style.display = "none";
        document.getElementById("verify_password").value = "";
        document.getElementById("verify_otp").value = "";
        document.getElementById("verify_otp").style.display = "none";
        document.getElementById("resendBtn").style.display = "none";
        document.getElementById("verifyBtn").innerText = "Confirm";
        clearInterval(countdownInterval);
        document.getElementById("otp-timer").style.display = "none";
        document.getElementById("otp-countdown").innerText = "02:00";
    };

    window.resendOTP = async function () {
        const password = document.getElementById("verify_password").value.trim();

        if (!sessionUser || !password) {
            showAlert("Email and password required to resend OTP", "error");
            return;
        }

        const result = await apiRequest("/request_otp", "POST", {
            username: sessionUser,
            password
        });

        if (result?.success) {
            showAlert("New OTP sent!", "success");
        } else {
            showAlert(result?.message || "Failed to resend OTP", "error");
        }
    };

    window.confirmVerification = async function () {
        const password = document.getElementById("verify_password").value.trim();
        const otpField = document.getElementById("verify_otp");

        if (!otpSent) {
            if (!sessionUser || !password) {
                showAlert("Password required", "error");
                return;
            }

            const result = await apiRequest("/request_otp", "POST", {
                username: sessionUser,
                password
            });

            if (result?.success) {
                showAlert("OTP sent. Check your email.", "success");
                otpSent = true;
                otpField.style.display = "block";
                document.getElementById("resendBtn").style.display = "inline-block";
                document.getElementById("verifyBtn").innerText = "Submit OTP";
                startOTPTimer();
            } else {
                showAlert(result?.message || "Invalid credentials", "error");
            }
        } else {
            const otp = otpField.value.trim();

            if (Date.now() > otpExpiryTime) {
                showAlert("OTP has expired. Please request a new one.", "error");
                return;
            }

            if (!otp) {
                showAlert("Enter the OTP sent to your email", "error");
                return;
            }

            if (pendingAction === "add") {
                runAddService(password, otp);
            } else if (pendingAction === "remove") {
                runRemoveService(password, otp);
            }

            otpSent = false;
            otpField.style.display = "none";
            document.getElementById("verifyBtn").innerText = "Confirm";
            closeModal();
        }
    };
});
