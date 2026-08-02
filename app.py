import streamlit as st
import google.generativeai as genai
import gspread
import datetime
import json
import os  # 👈 새로 추가된 부품입니다.

# 페이지 기본 설정
st.set_page_config(page_title="고전 탐구 대시보드", page_icon="📜", layout="wide")

# ==============================================================
# 🚨 선생님 설정 영역 (보안 금고 연동 완료!)
# ==============================================================
# 1. 금고에서 API 키 꺼내오기
GEMINI_API_KEY = st.secrets["gemini_api_key"]
SHEET_URL = "https://docs.google.com/spreadsheets/d/18bM8BHJcpF5FV3Z2EFctz4poLYGppfzrnePlY4g-Xto/edit?gid=0#gid=0"

# 2. 금고에 저장해둔 구글 인증 텍스트를 임시 파일로 만들어주는 마법의 코드
if not os.path.exists('credentials.json'):
    with open('credentials.json', 'w', encoding='utf-8') as f:
        f.write(st.secrets["credentials"])
        
if not os.path.exists('token.json'):
    with open('token.json', 'w', encoding='utf-8') as f:
        f.write(st.secrets["token"])
# ==============================================================

# Gemini AI 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-3.5-flash-lite')

@st.cache_resource
def get_sheet():
    gc = gspread.oauth(
        credentials_filename='credentials.json',
        authorized_user_filename='token.json'
    )
    return gc.open_by_url(SHEET_URL)

# 로그인 및 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.page = 1
    st.session_state.unlocked_page = 1

# =====================================================================
# 💾 진행 상황 저장 함수 (오류 방지 로직 적용)
# =====================================================================
def save_progress():
    try:
        doc = get_sheet()
        ws = doc.worksheet("Progress_DB")
        
        state_data = {
            "page": st.session_state.page,
            "unlocked_page": st.session_state.unlocked_page,
            "career": st.session_state.get("career", ""),
            "value_choice": st.session_state.get("value_choice", ""),
            "matched_works": st.session_state.get("matched_works", []),
            "selected_work": st.session_state.get("selected_work", None),
            "bg_knowledge": st.session_state.get("bg_knowledge", ""),
            "reason": st.session_state.get("reason", ""),
            "phrase": st.session_state.get("phrase", ""),
            "lesson": st.session_state.get("lesson", ""),
            "ai_perspectives": st.session_state.get("ai_perspectives", ""),
            "chosen_perspective_text": st.session_state.get("chosen_perspective_text", ""),
            "final_report": st.session_state.get("final_report", "")
        }
        json_str = json.dumps(state_data, ensure_ascii=False)
        
        # 💡 수정된 부분: 에러에 의존하지 않고 리스트로 검색하여 덮어쓰거나 새로 추가
        col_values = ws.col_values(1)
        if st.session_state.student_id in col_values:
            row_idx = col_values.index(st.session_state.student_id) + 1
            ws.update(f'B{row_idx}:C{row_idx}', [[st.session_state.student_name, json_str]])
        else:
            ws.append_row([st.session_state.student_id, st.session_state.student_name, json_str])
            
    except Exception as e:
        pass

# =====================================================================
# Step 0: 로그인 화면 (오류 방지 로직 적용)
# =====================================================================
if not st.session_state.logged_in:
    st.title("📜 고전 가치 탐구 프로젝트")
    st.subheader("👨‍🎓 학생 로그인")
    st.info("이름과 학번을 입력하면, 이전 진행 상황부터 이어서 할 수 있습니다.")
    
    with st.form("login_form"):
        s_id = st.text_input("학번 (예: 30101)")
        s_name = st.text_input("이름")
        submitted = st.form_submit_button("시작하기 / 이어하기 ➔")
        
        if submitted:
            if not s_id or not s_name:
                st.warning("학번과 이름을 모두 입력해주세요.")
            else:
                with st.spinner("진행 상황을 확인 중입니다..."):
                    try:
                        doc = get_sheet()
                        ws = doc.worksheet("Progress_DB")
                        
                        # 💡 수정된 부분: gspread 버전 충돌을 막기 위해 리스트에서 안전하게 검색
                        col_values = ws.col_values(1)
                        if s_id in col_values:
                            row_idx = col_values.index(s_id) + 1
                            row_vals = ws.row_values(row_idx)
                            
                            if len(row_vals) >= 3 and row_vals[1] == s_name:
                                state_data = json.loads(row_vals[2])
                                for k, v in state_data.items():
                                    st.session_state[k] = v
                                st.success("이전 진행 상황을 성공적으로 불러왔습니다!")
                        else:
                            st.success("새로운 탐구를 시작합니다!")
                    except Exception:
                        pass
                    
                    st.session_state.student_id = s_id
                    st.session_state.student_name = s_name
                    st.session_state.logged_in = True
                    st.rerun()
    st.stop()

# =====================================================================
# 🗺️ 수평형 프로세스 내비게이션 UI (상단 배치)
# =====================================================================
st.title("📜 고전 가치 탐구 프로젝트")

col_info, col_logout = st.columns([8, 1])
with col_info:
    st.markdown(f"**👤 접속자:** {st.session_state.student_id} {st.session_state.student_name}")
with col_logout:
    if st.button("로그아웃", key="logout_btn", use_container_width=True):
        st.session_state.clear()
        st.rerun()

st.markdown("---")
st.caption("🚀 **과정 중심 평가 전개 흐름** (클릭하여 이전 단계로 이동 및 수정 가능)")

step_cols = st.columns(5)
step_labels = ["1️⃣ 가치 설정", "2️⃣ 작품 선택", "3️⃣ 탐구 초안", "4️⃣ 관점 선택", "5️⃣ 최종 보고서"]

for i in range(1, 6):
    with step_cols[i-1]:
        if i == st.session_state.page:
            st.button(f"{step_labels[i-1]}", key=f"nav_{i}", disabled=True, type="primary", use_container_width=True)
        elif i <= st.session_state.unlocked_page:
            if st.button(f"{step_labels[i-1]}", key=f"nav_{i}", use_container_width=True):
                st.session_state.page = i
                st.rerun()
        else:
            st.button(f"🔒 미해제", key=f"nav_{i}", disabled=True, use_container_width=True)
            
st.markdown("---")

# =====================================================================
# Step 1: 진로 및 가치 설정 (수정 시 도미노 리셋)
# =====================================================================
if st.session_state.page == 1:
    st.subheader("💡 1단계: 나의 진로와 탐구 가치 설정")
    
    old_career = st.session_state.get('career', '')
    old_value = st.session_state.get('value_choice', '선택해주세요')
    
    with st.form("step1_form"):
        new_career = st.text_input("희망 진로 (예: 간호사, 소프트웨어 개발자 등)", value=old_career)
        
        options = ["선택해주세요", "관점(패러다임)의 전환", "사회 구조적 모순 개혁", "탈권위주의적 평등", "지식인의 도덕성 회복", "실용적 경제·기술 혁신", "절제와 분수의 미덕", "주체적 자아 성찰", "위기 대응 및 예방", "공정하고 수평적인 인재 활용", "직업 윤리와 평등", "신용과 정직의 가치", "비판적 사고와 역발상", "포용적 수용과 리더십", "생명 존중과 공존", "환경과 교육의 중요성", "변화의 수용과 달관", "소유의 상대성과 공공성", "균형 잡힌 리더십과 직언", "재물에 대한 올바른 경제관", "진정성 있는 인간관계"]
        default_index = options.index(old_value) if old_value in options else 0
        new_value = st.selectbox("탐구하고 싶은 인문학적 가치를 선택하세요", options, index=default_index)
        
        submitted = st.form_submit_button("저장하고 2단계로 이동 ➔")

        if submitted:
            if new_value == "선택해주세요" or not new_career:
                st.warning("모든 칸을 올바르게 입력해 주세요!")
            else:
                if new_career != old_career or new_value != old_value:
                    st.session_state.matched_works = []
                    st.session_state.selected_work = None
                    st.session_state.bg_knowledge = ""
                    st.session_state.reason = ""
                    st.session_state.phrase = ""
                    st.session_state.lesson = ""
                    st.session_state.ai_perspectives = ""
                    st.session_state.chosen_perspective_text = ""
                    st.session_state.final_report = ""
                    st.session_state.unlocked_page = 2
                
                st.session_state.career = new_career
                st.session_state.value_choice = new_value
                
                doc = get_sheet()
                ws_rag = doc.worksheet("RAG_DB")
                records = ws_rag.get_all_records()
                
                matched = []
                for row in records:
                    if st.session_state.value_choice in str(row.get('핵심 가치 키워드', '')):
                        matched.append(row)
                        if len(matched) == 2:
                            break
                st.session_state.matched_works = matched
                
                if not matched:
                    st.error("선택한 가치에 해당하는 고전 작품이 데이터베이스에 없습니다.")
                else:
                    st.session_state.page = 2
                    if st.session_state.unlocked_page < 2:
                        st.session_state.unlocked_page = 2
                    save_progress()
                    st.rerun()

# =====================================================================
# Step 2: 작품 선택 (수정 시 도미노 리셋)
# =====================================================================
elif st.session_state.page == 2:
    st.subheader("📚 2단계: 탐구할 고전 작품 선택")
    st.info(f"선택한 핵심 가치 **'{st.session_state.value_choice}'**가 담긴 작품들입니다. 두 작품을 비교해 보고 하나를 선택하세요.")
    
    works = st.session_state.matched_works
    cols = st.columns(len(works))
    
    for idx, work in enumerate(works):
        with cols[idx]:
            st.markdown(f"### 📖 {work.get('작품명', '')}")
            st.caption(f"저자: {work.get('저자', '')}")
            with st.expander("원문 보기"):
                st.write(work.get('원문', ''))
            with st.expander("현대어 풀이 보기"):
                st.write(work.get('현대어 풀이', ''))
            
            if st.button(f"👉 '{work.get('작품명', '')}' 탐구하기", key=f"select_{idx}", use_container_width=True):
                if work != st.session_state.get('selected_work'):
                    st.session_state.bg_knowledge = ""
                    st.session_state.reason = ""
                    st.session_state.phrase = ""
                    st.session_state.lesson = ""
                    st.session_state.ai_perspectives = ""
                    st.session_state.chosen_perspective_text = ""
                    st.session_state.final_report = ""
                    st.session_state.unlocked_page = 3
                
                st.session_state.selected_work = work
                st.session_state.page = 3
                if st.session_state.unlocked_page < 3:
                    st.session_state.unlocked_page = 3
                save_progress()
                st.rerun()

# =====================================================================
# Step 3: 배경지식 및 초안 작성 (수정 시 도미노 리셋)
# =====================================================================
elif st.session_state.page == 3:
    work = st.session_state.selected_work
    title = work.get('작품명', '')
    author = work.get('저자', '')
    
    st.subheader(f"🧠 3단계: '{title}' 심층 탐구 초안 작성")
    
    if not st.session_state.bg_knowledge:
        with st.spinner("AI가 작가와 저술 배경에 대한 지식을 가져오는 중입니다..."):
            prompt_bg = f"너는 한문 교사야. 학생들을 위해 고전 산문 '{title}'(저자: {author})에 대한 사전적 배경지식(작가의 생애 특징, 이 글을 쓰게 된 시대적/개인적 저술 배경)을 고등학생이 이해하기 쉽게 3~4문장으로 요약해 줘."
            response = model.generate_content(prompt_bg)
            st.session_state.bg_knowledge = response.text

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("#### 📜 작품 원문 및 해석")
        st.info(f"**[원문]**\n{work.get('원문', '')}")
        st.success(f"**[현대어 풀이]**\n{work.get('현대어 풀이', '')}")
    with col2:
        st.markdown("#### 🏛️ 작가 및 저술 배경 (AI 보조)")
        st.write(st.session_state.bg_knowledge)
        
    st.markdown("---")
    st.markdown("#### ✍️ 나의 탐구 초안 작성")
    
    old_reason = st.session_state.get('reason', '')
    old_phrase = st.session_state.get('phrase', '')
    old_lesson = st.session_state.get('lesson', '')
    
    with st.form("draft_form"):
        new_reason = st.text_area("1. 선정 이유 (이 작품의 어떤 점이 나의 호기심을 끌었나요?)", value=old_reason)
        new_phrase = st.text_input("2. 인상 깊은 구절 (가장 와닿는 원문이나 해석을 적어주세요)", value=old_phrase)
        new_lesson = st.text_area("3. 도출할 수 있는 가치나 교훈 (나의 삶이나 현대 사회와 연결해 보세요)", value=old_lesson)
        
        submitted = st.form_submit_button("저장하고 4단계 관점 추천받기 ➔")
        
        if submitted:
            if not new_reason or not new_phrase or not new_lesson:
                st.warning("모든 칸을 작성해 주세요!")
            else:
                if new_reason != old_reason or new_phrase != old_phrase or new_lesson != old_lesson:
                    st.session_state.ai_perspectives = ""
                    st.session_state.chosen_perspective_text = ""
                    st.session_state.final_report = ""
                    st.session_state.unlocked_page = 4
                
                st.session_state.reason = new_reason
                st.session_state.phrase = new_phrase
                st.session_state.lesson = new_lesson
                st.session_state.page = 4
                if st.session_state.unlocked_page < 4:
                    st.session_state.unlocked_page = 4
                save_progress()
                st.rerun()

# =====================================================================
# Step 4: 탐구 관점 생성 및 선택 (수정 시 도미노 리셋)
# =====================================================================
elif st.session_state.page == 4:
    st.subheader("🧭 4단계: 진로 연계 탐구 관점 선택")
    
    if not st.session_state.ai_perspectives:
        with st.spinner(f"'{st.session_state.career}' 진로에 맞춘 탐구 방향을 생성하고 있습니다..."):
            prompt_perspectives = f"""
            너는 학생의 진로 융합 탐구를 돕는 교사야. 
            학생 희망 진로: {st.session_state.career}
            작품: {st.session_state.selected_work.get('작품명')}
            학생이 도출한 교훈: {st.session_state.lesson}
            
            이 내용을 바탕으로 학생이 깊이 있는 사고를 할 수 있도록 서로 다른 3가지 탐구 관점을 제시해 줘.
            [규칙]
                1. 어려운 학술 용어나 전문 기술 용어는 제외하되, 고등학생 수준에서 탐구할 수 있을 만한 용어를 적극 활용할 것.
                2. 진로 핵심 역량과 작품의 핵심 제재를 유기적으로 연결할 것.
                3. 반드시 아래의 세부 형식과 기호를 정확히 지켜서 출력할 것. (관점과 관점 사이에는 반드시 '@@@' 기호만 넣을 것)
                
                [관점 1] 🔴 **핵심 키워드**: (관점 요약)
                - 💡 **설명**: (해당 관점에 대한 구체적인 심화 설명)
                - 🎯 **탐구주제**: "고등학교 수준의 매력적인 탐구 제목"
                @@@
                [관점 2] 🔵 **핵심 키워드**: (관점 요약)
                - 💡 **설명**: (해당 관점에 대한 구체적인 심화 설명)
                - 🎯 **탐구주제**: "고등학교 수준의 매력적인 탐구 제목"
                @@@
                [관점 3] 🟢 **핵심 키워드**: (관점 요약)
                - 💡 **설명**: (해당 관점에 대한 구체적인 심화 설명)
                - 🎯 **탐구주제**: "고등학교 수준의 매력적인 탐구 제목"
            """
            response = model.generate_content(prompt_perspectives)
            st.session_state.ai_perspectives = response.text

    raw_text = st.session_state.ai_perspectives
    perspectives_list = raw_text.split("@@@")
    
    p1 = perspectives_list[0].strip() if len(perspectives_list) > 0 else "관점 1 생성 오류"
    p2 = perspectives_list[1].strip() if len(perspectives_list) > 1 else "관점 2 생성 오류"
    p3 = perspectives_list[2].strip() if len(perspectives_list) > 2 else "관점 3 생성 오류"

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("#### 💡 AI 제안 탐구 관점")
        with st.container(border=True):
            st.markdown(p1)
        with st.container(border=True):
            st.markdown(p2)
        with st.container(border=True):
            st.markdown(p3)
            
    with col2:
        st.markdown("#### 🎯 관점 선택")
        
        prev_chosen = st.session_state.get('chosen_perspective', '관점 1')
        options = ["관점 1", "관점 2", "관점 3", "나만의 새로운 관점"]
        default_index = options.index(prev_chosen) if prev_chosen in options else 0
        
        with st.form("perspective_form"):
            chosen_perspective = st.radio("어떤 관점을 중심으로 최종 보고서를 작성하시겠습니까?", options, index=default_index)
            submitted = st.form_submit_button("저장하고 5단계로 이동 ➔")
            
            if submitted:
                if "관점 1" in chosen_perspective:
                    selected_text = p1
                elif "관점 2" in chosen_perspective:
                    selected_text = p2
                elif "관점 3" in chosen_perspective:
                    selected_text = p3
                else:
                    selected_text = "사용자 직접 작성 관점"
                
                if selected_text != st.session_state.get('chosen_perspective_text'):
                    st.session_state.final_report = ""
                
                st.session_state.chosen_perspective = chosen_perspective
                st.session_state.chosen_perspective_text = selected_text
                st.session_state.page = 5
                if st.session_state.unlocked_page < 5:
                    st.session_state.unlocked_page = 5
                save_progress()
                st.rerun()

# =====================================================================
# Step 5: 최종 보고서 작성 및 구글 시트 전송
# =====================================================================
elif st.session_state.page == 5:
    st.subheader("🎓 5단계: 최종 탐구 보고서 작성")
    
    st.markdown("#### 📌 내가 선택한 탐구 관점")
    with st.container(border=True):
        st.markdown(st.session_state.chosen_perspective_text)
    
    st.markdown("위 방향성을 참고하여, 앞서 작성한 선정 이유와 교훈을 유기적으로 연결한 한 편의 글을 완성해 보세요.")
    
    old_report = st.session_state.get('final_report', '')
    
    with st.form("final_report_form"):
        final_report = st.text_area("최종 탐구 결과 보고서", value=old_report, height=300)
        final_submit = st.form_submit_button("🚀 최종 제출하기")

        if final_submit:
            if not final_report:
                st.warning("보고서 내용을 작성해 주세요!")
            else:
                st.session_state.final_report = final_report
                save_progress()
                
                with st.spinner("최종 결과물을 구글 시트에 저장하고 있습니다..."):
                    try:
                        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        doc = get_sheet()
                        ws_results = doc.worksheet("Student_Results")
                        
                        row_data = [
                            now, 
                            st.session_state.student_id, 
                            st.session_state.student_name, 
                            st.session_state.career,               
                            st.session_state.value_choice, 
                            f"{st.session_state.selected_work.get('작품명')} ({st.session_state.selected_work.get('저자')})",
                            st.session_state.reason,
                            st.session_state.phrase,
                            st.session_state.lesson,
                            st.session_state.chosen_perspective_text, 
                            final_report
                        ]
                        ws_results.append_row(row_data)
                        
                        st.balloons()
                        st.success("🎉 성공적으로 제출되었습니다! 선생님의 구글 시트에 안전하게 기록되었습니다.")
                    except Exception as e:
                        st.error(f"제출 중 오류가 발생했습니다: {e}")
