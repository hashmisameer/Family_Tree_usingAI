document.addEventListener("DOMContentLoaded", () => {
    // Toggle Add Member Form
    const toggleAddMemberForm = document.getElementById("toggle-add-member-form");
    const addMemberForm = document.getElementById("add-member-form");

    // Ensure that the form exists and the toggle button is available
    if (toggleAddMemberForm && addMemberForm) {
        toggleAddMemberForm.addEventListener("click", () => {
            const isVisible = addMemberForm.style.display === "block";
            addMemberForm.style.display = isVisible ? "none" : "block";
        });
    }

    // Hamburger Menu Toggle
    const menuToggle = document.getElementById("menu-toggle");
    const sidebar = document.querySelector(".dashboard-sidebar"); // Ensure correct class reference for the sidebar
    const mainContent = document.querySelector(".dashboard-main");

    // Ensure the sidebar and main content elements exist
    if (menuToggle && sidebar && mainContent) {
        menuToggle.addEventListener("click", () => {
            sidebar.classList.toggle("sidebar-active");
            mainContent.classList.toggle("content-expanded");
        });
    }

    // Pie Chart Initialization (Ensure that the chart element exists)
    const pieChartCanvas = document.getElementById("familyPieChart");
    if (pieChartCanvas) {
        const ctx = pieChartCanvas.getContext("2d");
        new Chart(ctx, {
            type: "pie",
            data: {
                labels: ["Males", "Females", "Children"], // Replace with dynamic values if available
                datasets: [{
                    data: [50, 40, 10], // Replace with dynamic values if available
                    backgroundColor: ["#4CAF50", "#2196F3", "#FF9800"],
                    hoverOffset: 4,
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: "top",
                    },
                    title: {
                        display: true,
                        text: "Family Member Distribution"
                    }
                }
            }
        });
    }

});
