document.addEventListener("DOMContentLoaded", function () {
    // Utility function to show a loader
    function showLoader() {
        let loader = document.createElement("div");
        loader.classList.add("loader");
        loader.innerHTML = "Processing...";
        document.body.appendChild(loader);
    }

    // Utility function to remove the loader
    function removeLoader() {
        let loader = document.querySelector(".loader");
        if (loader) loader.remove();
    }

    // Utility function to show alert messages
    function showAlert(message, type = "info") {
        let alertBox = document.createElement("div");
        alertBox.classList.add("alert", type);
        alertBox.innerText = message;
        document.body.appendChild(alertBox);

        setTimeout(() => {
            alertBox.remove();
        }, 3000);
    }

    // Generic fetch function to handle API calls
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

    // Login Function
    window.login = async function () {
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();

        if (!username || !password) {
            showAlert("Please enter username and password!", "error");
            return;
        }

        const data = await apiRequest("/login", "POST", { username, password });

        if (data?.success) {
            showAlert(data.message, "success");
            setTimeout(() => window.location.href = "/dashboard", 1000);
        } else {
            showAlert(data.message, "error");
        }
    };

    // Register Function
    window.register = async function () {
        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();

        if (!username || !password) {
            showAlert("Please enter username and password!", "error");
            return;
        }

        const data = await apiRequest("/register", "POST", { username, password });
        showAlert(data?.message || "Registration failed!", data?.success ? "success" : "error");
    };

    // Add Service Function
    window.addService = async function () {
        const serviceName = document.getElementById("service_name").value.trim();
        const serviceIp = document.getElementById("service_ip").value.trim();
        const servicePort = document.getElementById("service_port").value.trim();
        const addButton = document.querySelector(".add-btn");

        if (!serviceName || !serviceIp || !servicePort) {
            showAlert("All fields are required!", "error");
            return;
        }

        const data = await apiRequest("/add_service", "POST", {
            service_name: serviceName,
            service_ip: serviceIp,
            service_port: servicePort
        });

        if (data?.success) {
            showAlert(data.message, "success");

            // Disable the add button
            addButton.disabled = true;

            // Create "Add Another Service" button
            let addAnotherBtn = document.createElement("button");
            addAnotherBtn.innerText = "Want to add another?";
            addAnotherBtn.classList.add("add-another-btn");
            addAnotherBtn.onclick = () => location.reload();

            document.querySelector(".add-service").appendChild(addAnotherBtn);
        } else {
            showAlert(data?.message || "Failed to add service!", "error");
        }
    };

    // Remove Service Function
    window.removeService = async function () {
        const serviceName = document.getElementById("remove_service_name").value.trim();

        if (!serviceName) {
            showAlert("Service name is required!", "error");
            return;
        }

        const data = await apiRequest("/remove_service", "POST", { service_name: serviceName });
        showAlert(data?.message || "Failed to remove service!", data?.success ? "success" : "error");
    };

    // Logout function
    window.logout = function () {
        window.location.href = "/logout";
    };
});
