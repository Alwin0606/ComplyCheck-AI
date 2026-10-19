
async function loadHealth() {
    const badge = document.getElementById("healthBadge");
    const message = document.getElementById("healthMessage");

    try {
        const response = await fetch("/api/health");

        if (!response.ok) {
            throw new Error("API returned HTTP " + response.status);
        }

        const data = await response.json();

        document.getElementById("deviceName").textContent = data.device;
        document.getElementById("osName").textContent = data.operating_system;

        document.getElementById("cpuValue").textContent = Number(data.cpu_usage).toFixed(1);
        document.getElementById("cpuBar").style.width = data.cpu_usage + "%";

        document.getElementById("memoryValue").textContent = Number(data.memory_usage).toFixed(1);
        document.getElementById("memoryBar").style.width = data.memory_usage + "%";
        document.getElementById("memoryNote").textContent =
            data.memory_total_gb + " GB total RAM";

        document.getElementById("diskValue").textContent = Number(data.disk_usage).toFixed(1);
        document.getElementById("diskBar").style.width = data.disk_usage + "%";
        document.getElementById("diskNote").textContent =
            data.disk_free_gb + " GB free";

        badge.textContent = data.status.toUpperCase();

        message.textContent = data.warnings.length
            ? data.warnings.join(". ")
            : "Your laptop is healthy.";

        const list = document.getElementById("recommendations");
        list.innerHTML = "";

        if (data.warnings.length) {
            data.warnings.forEach((warning) => {
                const item = document.createElement("li");
                item.textContent = warning;
                list.appendChild(item);
            });
        } else {
            list.innerHTML = "<li>No major issues detected.</li>";
        }

        document.getElementById("lastUpdated").textContent =
            "Last scanned: " + new Date().toLocaleTimeString();

    } catch (error) {
        console.error("LaptopCare AI error:", error);

        badge.textContent = "ERROR";
        message.textContent = "Actual error: " + (error.message || String(error));
    }
}

document.getElementById("refreshBtn").addEventListener("click", loadHealth);

loadHealth();
setInterval(loadHealth, 5000);


             
