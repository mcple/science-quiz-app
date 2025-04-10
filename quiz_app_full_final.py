import streamlit as st
import pandas as pd
import random
import time
import os
import plotly.express as px

@st.cache_data
def load_questions():
    df = pd.read_excel("quiz_with_explanations_difficulty.xlsx")
    return df

df_all = load_questions()

st.title("📘 풀옵션 과학 퀴즈")

# 초기 설정
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
    st.session_state.selected_difficulty = None
    st.session_state.selected_count = 10

if not st.session_state.quiz_started:
    st.subheader("⚙️ 퀴즈 설정")
    st.session_state.username = st.text_input("🧑‍🎓 이름을 입력하세요:")

    difficulties = df_all["difficulty"].unique().tolist()
    st.session_state.selected_difficulty = st.selectbox("난이도 선택", ["전체"] + difficulties)
    st.session_state.selected_count = st.slider("출제할 문제 수", 1, min(20, len(df_all)), 10)

    if st.button("🚀 퀴즈 시작"):
        df_filtered = df_all if st.session_state.selected_difficulty == "전체" else df_all[df_all["difficulty"] == st.session_state.selected_difficulty]
        questions = df_filtered.sample(n=min(st.session_state.selected_count, len(df_filtered))).to_dict("records")
        random.shuffle(questions)
        st.session_state.questions = questions
        st.session_state.index = 0
        st.session_state.score = 0
        st.session_state.finished = False
        st.session_state.start_time = time.time()
        st.session_state.timing_log = []
        st.session_state.submitted = False
        st.session_state.quiz_started = True
        st.rerun()

elif not st.session_state.finished:
    q = st.session_state.questions[st.session_state.index]
    st.subheader(f"문제 {st.session_state.index + 1}: {q['question']}")
    st.caption(f"📶 난이도: {q.get('difficulty', '보통')}")

    # 실시간 타이머 (소수점 첫째 자리)
    elapsed = round(time.time() - st.session_state.start_time, 1)
    st.info(f"⏱️ 경과 시간: {elapsed}초")

    options = [q["option1"], q["option2"], q["option3"], q["option4"]]
    random.shuffle(options)

    for opt in options:
        if st.button(opt):
            time_taken = round(time.time() - st.session_state.start_time, 1)
            st.session_state.timing_log.append((q["question"], time_taken))

            if opt == q["answer"]:
                st.success("정답입니다!")
                st.session_state.score += 1
            else:
                st.error(f"오답입니다. 정답: {q['answer']}")
            st.info(f"📘 해설: {q['explanation']}")

            if st.session_state.index < len(st.session_state.questions) - 1:
                st.session_state.index += 1
                st.session_state.start_time = time.time()
            else:
                st.session_state.finished = True
            st.rerun()

else:
    st.success(f"퀴즈 완료! 점수: {st.session_state.score} / {len(st.session_state.questions)}")
    st.subheader("⏱️ 문제별 풀이 시간")
    for i, (qt, sec) in enumerate(st.session_state.timing_log, 1):
        st.write(f"{i}. {qt[:30]}... ⏰ {sec}초")

    st.subheader("📊 성취도 분석")
    df_chart = pd.DataFrame({
        "문항": [f"{i+1}" for i in range(len(st.session_state.timing_log))],
        "풀이 시간(초)": [sec for _, sec in st.session_state.timing_log]
    })
    fig = px.bar(df_chart, x="문항", y="풀이 시간(초)", text="풀이 시간(초)", title="문제별 풀이 시간")
    st.plotly_chart(fig, use_container_width=True)

    if not st.session_state.submitted and st.button("✅ 결과 저장"):
        timing_summary = "; ".join([f"{i+1}:{sec}s" for i, (_, sec) in enumerate(st.session_state.timing_log)])
        row = pd.DataFrame([[st.session_state.username, st.session_state.score, timing_summary]], columns=["이름", "점수", "문제별 시간"])
        try:
            df_old = pd.read_csv("quiz_scores.csv")
            df = pd.concat([df_old, row], ignore_index=True)
        except FileNotFoundError:
            df = row
        df.to_csv("quiz_scores.csv", index=False)
        st.success("✅ 저장 완료!")
        st.session_state.submitted = True

    if os.path.exists("quiz_scores.csv"):
        df_hist = pd.read_csv("quiz_scores.csv")
        st.write("📚 전체 기록:")
        st.dataframe(df_hist, height=300)

    if st.button("🔁 다시 시작"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()