document.addEventListener("DOMContentLoaded", () => {
    const presetPills = document.getElementById("presetPills");
    const userQuery = document.getElementById("userQuery");
    const runBtn = document.getElementById("runBtn");
    const baselineBody = document.getElementById("baselineBody");
    const reactBody = document.getElementById("reactBody");

    let testCasesData = [];

    // Tải danh sách Test Cases từ API Server
    async function loadTestCases() {
        try {
            const res = await fetch("/api/test-cases");
            testCasesData = await res.json();
            renderPills(testCasesData);
        } catch (err) {
            console.error("Không thể tải test cases:", err);
        }
    }

    function renderPills(cases) {
        presetPills.innerHTML = "";

        const groups = [
            {
                title: "📚 Nhóm 1: Hỏi đáp & Khám phá nhân cách cơ bản (#1 - #6)",
                filter: item => item.id >= 1 && item.id <= 6
            },
            {
                title: "⚔️ Nhóm 2: Tâm lý mâu thuẫn phức tạp & Phác đồ (#7 - #9)",
                filter: item => item.id >= 7 && item.id <= 9
            },
            {
                title: "🛡️ Nhóm 3: Edge Cases, Bẫy Guardrail & Red Flag Khẩn cấp (#10 - #15)",
                filter: item => item.id >= 10 && item.id <= 15
            }
        ];

        groups.forEach(group => {
            const groupSection = document.createElement("div");
            groupSection.className = "test-group-section";

            const groupHeader = document.createElement("div");
            groupHeader.className = "group-header";
            groupHeader.innerHTML = `<span class="group-title">${escapeHtml(group.title)}</span>`;
            groupSection.appendChild(groupHeader);

            const pillsContainer = document.createElement("div");
            pillsContainer.className = "group-pills";

            const items = cases.filter(group.filter);
            items.forEach(item => {
                const btn = document.createElement("button");
                btn.className = "pill-btn";
                btn.innerHTML = `<strong class="pill-id">#${item.id}</strong> <span class="pill-text">${escapeHtml(item.question)}</span>`;
                btn.title = `[${item.category}] ${item.question}`;
                btn.addEventListener("click", () => {
                    document.querySelectorAll(".pill-btn").forEach(p => p.classList.remove("active"));
                    btn.classList.add("active");
                    userQuery.value = item.question;
                });
                pillsContainer.appendChild(btn);
            });

            groupSection.appendChild(pillsContainer);
            presetPills.appendChild(groupSection);
        });
    }

    function getCategoryIcon(cat) {
        if (cat.includes("Hỏi đáp")) return "📚";
        if (cat.includes("Khám phá")) return "🔍";
        if (cat.includes("Tâm lý mâu thuẫn")) return "⚔️";
        if (cat.includes("Edge Case")) return "⚠️";
        if (cat.includes("Red Flag")) return "🚨";
        return "📝";
    }

    // Chạy so sánh song song
    async function runComparison() {
        const query = userQuery.value.trim();
        if (!query) return;

        // Trạng thái Loading
        runBtn.disabled = true;
        runBtn.querySelector(".btn-text").textContent = "⏳ Đang suy luận...";

        baselineBody.innerHTML = `
            <div class="placeholder-state">
                <span class="large-icon">🔄</span>
                <p>LLM Baseline đang tạo phản hồi...</p>
            </div>
        `;

        reactBody.innerHTML = `
            <div class="placeholder-state">
                <span class="large-icon">🧠</span>
                <p>ReAct Agent đang suy luận chuỗi Thought -> Action -> Observation...</p>
            </div>
        `;

        try {
            // Gọi song song 2 API
            const [baselineRes, reactRes] = await Promise.all([
                fetch("/api/chat/baseline", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ query })
                }).then(r => r.json()),
                fetch("/api/chat/react", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ query })
                }).then(r => r.json())
            ]);

            // Render Baseline Column
            renderBaseline(baselineRes.response);

            // Render ReAct Column (Animated)
            renderReactSteps(reactRes);

        } catch (err) {
            console.error("Lỗi khi chạy so sánh:", err);
            baselineBody.innerHTML = `<div class="guardrail-alert">⚠️ Lỗi kết nối server: ${err.message}</div>`;
            reactBody.innerHTML = `<div class="guardrail-alert">⚠️ Lỗi kết nối server: ${err.message}</div>`;
        } finally {
            runBtn.disabled = false;
            runBtn.querySelector(".btn-text").textContent = "🚀 Chạy So Sánh";
        }
    }

    function renderMarkdown(text) {
        if (!text) return "";
        if (typeof marked !== "undefined" && typeof marked.parse === "function") {
            return marked.parse(text);
        }
        return escapeHtml(text);
    }

    function renderBaseline(responseText) {
        baselineBody.innerHTML = `
            <div class="response-box markdown-content">
                ${renderMarkdown(responseText)}
            </div>
        `;
    }

    function renderReactSteps(data) {
        reactBody.innerHTML = "";

        if (!data.steps || data.steps.length === 0) {
            reactBody.innerHTML = `<div class="placeholder-state"><p>Không có bước suy luận nào.</p></div>`;
            return;
        }

        data.steps.forEach(step => {
            const card = document.createElement("div");
            card.className = "step-card";

            let html = `
                <div class="step-header">
                    <span>🔄 Vòng lặp ReAct (Step ${step.step_number}/${step.max_steps})</span>
                </div>
            `;

            if (step.thought) {
                html += `
                    <div class="thought-block">
                        <strong>🧠 Thought:</strong> ${escapeHtml(step.thought)}
                    </div>
                `;
            }

            if (step.action) {
                html += `
                    <div class="action-block">
                        <strong>🛠️ Action:</strong> ${escapeHtml(step.action)}
                    </div>
                `;
            }

            if (step.observation) {
                const obsText = typeof step.observation.parsed === "object" 
                    ? JSON.stringify(step.observation.parsed, null, 2) 
                    : (step.observation.raw || "");
                html += `
                    <div class="observation-block">
                        <strong>👁️ Observation:</strong>
                        <pre>${escapeHtml(obsText)}</pre>
                    </div>
                `;
            }

            card.innerHTML = html;
            reactBody.appendChild(card);
        });

        // Nếu có Final Answer
        if (data.final_answer) {
            const finalCard = document.createElement("div");
            finalCard.className = "final-answer-card";
            finalCard.innerHTML = `
                <div class="final-answer-header">
                    🏁 Final Answer (Câu trả lời cuối cùng)
                </div>
                <div class="markdown-content" style="line-height: 1.6;">
                    ${renderMarkdown(data.final_answer)}
                </div>
            `;
            reactBody.appendChild(finalCard);
        }

        // Nếu Guardrail bị kích hoạt
        if (data.guardrail_triggered) {
            const alertCard = document.createElement("div");
            alertCard.className = "guardrail-alert";
            alertCard.innerHTML = `
                🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa bước suy luận. Ngắt lặp an toàn!
            `;
            reactBody.appendChild(alertCard);
        }
    }

    function escapeHtml(str) {
        return (str || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    runBtn.addEventListener("click", runComparison);
    userQuery.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            runComparison();
        }
    });

    loadTestCases();
});
