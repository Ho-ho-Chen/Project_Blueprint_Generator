# ==========================================
# config.py: 提示詞與設定
# ==========================================

# AI 架構師的人設與指令
ARCHITECT_PROMPT = """
你是矽谷頂級軟體架構師 (CTO)。使用者想開發一個新專案，點子是：「{idea}」。

請為這個專案生成一份完整的「開發藍圖」，必須包含以下 4 大文件內容。
請嚴格以 JSON 格式輸出 (不要 Markdown 標記)，包含以下欄位：

1. "project_name": 專案名稱 (英/中)
2. "description": 專案描述與願景 (200字)
3. "values": 核心價值 (列點)
4. "tech_stack": 推薦技術棧 (Frontend, Backend, DB, AI)
5. "structure_tree": 檔案目錄結構樹 (文字呈現)
6. "data_schema": 核心資料結構 (JSON Schema 範例)
7. "todo_phase1": 第一階段 MVP 任務清單
8. "todo_phase2": 第二階段 擴充任務清單
9. "risk_log": 初始風險評估與開發注意事項

JSON 範例結構：
{{
    "project_name": "...",
    "description": "...",
    "values": "...",
    "tech_stack": "...",
    "structure_tree": "...",
    "data_schema": "...",
    "todo_phase1": "...",
    "todo_phase2": "...",
    "risk_log": "..."
}}
"""

# 預設值 (當 AI 尚未生成時顯示)
DEFAULT_BLUEPRINT = {
    "project_name": "新專案名稱",
    "description": "請輸入您的點子，AI 將自動為您撰寫描述...",
    "values": "- 價值 1\n- 價值 2",
    "tech_stack": "Python, Streamlit...",
    "structure_tree": "app.py\nconfig.py...",
    "data_schema": "{}",
    "todo_phase1": "- [ ] 任務 1",
    "todo_phase2": "- [ ] 任務 2",
    "risk_log": "無"
}
