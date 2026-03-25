import gradio as gr
import asyncio
import os
import httpx
import tempfile

from run import csv_mode, city_mode, multi_city_mode

os.environ['LANG'] = 'en_US.UTF-8'

FASTAPI_URL = "http://127.0.0.1:8000"
POLLING_INTERVAL = 3


# 이 코드는 Gradio UI의 백그라운드에서 실행됩니다.
js_code = """
<script>
function set_job_id(job_id) {
    if (job_id) {
        sessionStorage.setItem('current_job_id', job_id);
    } else {
        sessionStorage.removeItem('current_job_id');
    }
    return job_id;
}

function get_job_id() {
    return sessionStorage.getItem('current_job_id');
}
</script>
"""


async def handle_submit_api(city_name: str = None, csv_file = None, job_id_from_browser: str = None):
    job_id = None

    # --- 분기 로직: 새 작업 시작 vs 기존 작업 확인 ---
    if job_id_from_browser:
        # 페이지 새로고침 시: 브라우저에 저장된 job_id로 시작
        job_id = job_id_from_browser
        yield f"⏳ 이전 작업 상태를 확인 중... (Job ID: {job_id[:8]}...)", gr.update(visible=False), job_id
    elif city_name or csv_file:
        # 버튼 클릭 시: 새로운 분석 시작
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if city_name:
                    response = await client.post(f"{FASTAPI_URL}/city", json={"city": city_name})
                else:
                    files = {'file': (os.path.basename(csv_file.name), open(csv_file.name, 'rb'), 'text/csv')}
                    response = await client.post(f"{FASTAPI_URL}/csv", files=files)
                response.raise_for_status()
                job_id = response.json().get("job_id")
        except httpx.RequestError as e:
            yield f"❌ 서버 연결 실패: {e}", gr.update(visible=False), None
            return
        
        if not job_id:
            yield "❌ Job ID를 받아오지 못했습니다.", gr.update(visible=False), None
            return
        
        yield f"⏳ 분석이 시작되었습니다.", gr.update(visible=False), job_id
    else:
        # 초기 로드 시 (저장된 job_id 없음)
        yield "분석할 도시 이름 또는 CSV 파일을 입력하세요.", gr.update(visible=False), None
        return

    # --- 공통 상태 확인 루프 ---
    while True:
        await asyncio.sleep(POLLING_INTERVAL)
        try:
            async with httpx.AsyncClient() as client:
                status_response = await client.get(f"{FASTAPI_URL}/status/{job_id}")
                status_response.raise_for_status()
                status_data = status_response.json()
            
            status = status_data.get("status")

            if status == "completed":
                filename = status_data.get("result_filename")
                download_url = f"{FASTAPI_URL}/download/{filename}"
                
                async with httpx.AsyncClient() as client:
                    download_response = await client.get(download_url)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
                    temp_file.write(download_response.content)
                    temp_file_path = temp_file.name

                success_message = f"## ✅ 분석 완료!\n\n결과 파일: `{filename}`"
                # **▼▼▼ 작업 완료 후 job_id를 None으로 초기화하여 JS 호출 ▼▼▼**
                yield success_message, gr.update(value=temp_file_path, visible=True), None
                break
            elif status == "failed":
                error_message = status_data.get("error", "알 수 없는 오류")
                # **▼▼▼ 작업 실패 후 job_id를 None으로 초기화하여 JS 호출 ▼▼▼**
                yield f"❌ 분석 실패: {error_message}", gr.update(visible=False), None
                break
            elif status == "running":
                 yield f"⏳ 분석 진행 중... (Job ID: {job_id[:8]}...)", gr.update(visible=False), job_id
            else:
                yield f"❓ 알 수 없는 상태: {status}", gr.update(visible=False), job_id

        except httpx.RequestError as e:
            yield f"❌ 상태 확인 중 서버 연결 실패: {e}", gr.update(visible=False), job_id
            break
    



theme = gr.themes.Soft(
    font=[gr.themes.GoogleFont("Inter"), "Arial", "sans-serif"]
)

# --- [수정] Gradio UI에 파일 다운로드 컴포넌트 추가 ---
with gr.Blocks(theme=theme, title="PM Analysis Agent") as demo:
    
    job_id_state = gr.Textbox(value="", visible=False)
    
    gr.Markdown("# 🏢 PM Analysis Agent")
    with gr.Tabs():
        with gr.TabItem("🏙️ Search by City Name"):
            gr.Markdown(
                """
                **🌆 Single or Multiple Cities:**
                - **Single city**: Enter one city name (e.g., `Springdale`)
                - **Multiple cities**: Enter comma-separated cities (e.g., `Milwaukee, Chicago, Detroit`)
                
                Multiple cities will be processed sequentially and results will be merged into a single CSV file.
                """
            )
            city_input = gr.Textbox(
                label="City Name(s)", 
                placeholder="e.g., Springdale or Milwaukee, Chicago, Detroit",
                info="Enter single city or comma-separated multiple cities"
            )
            city_button = gr.Button("Start Analysis", variant="primary")
        with gr.TabItem("📄 Search by CSV File"):
            gr.Markdown(
                """
                **⚠️ Important:** The uploaded CSV file must contain a header named **`Organization Name`**.
                Other columns like `City` are optional but can help improve search accuracy.

                **Example File:**
                | Organization Name       | City         | (Optional Columns...) |
                | ----------------------- | ------------ | --------------------- |
                | ABC Property Management | Springdale   | ...                   |
                | XYZ Realty              | Fayetteville | ...                   |
                """
            )
            with gr.Row():
                csv_input = gr.File(label="Upload a CSV file with organization names", file_types=['.csv'])
            with gr.Row():
                csv_button = gr.Button("Start Analysis", variant="primary")

    stop_button = gr.Button("Stop Analysis", variant="stop")
    gr.Markdown("---")
    gr.Markdown("## 📝 Results")

    result_output = gr.Markdown(label="Analysis Summary")
    download_output = gr.File(
        label="📥 Download Results as CSV", 
        visible=False, 
        interactive=True,
        type="filepath"
    )
    
    
    # JS 함수 set_job_id를 호출하여 sessionStorage에 값을 저장/삭제
    # job_id_state.change(fn=None, inputs=job_id_state, js="""
    #     (job_id) => {
    #         if (job_id) {
    #             sessionStorage.setItem('current_job_id', job_id);
    #         } else {
    #             sessionStorage.removeItem('current_job_id');
    #         }
    #         return job_id;
    #     }
    #     """)
    
    city_event = city_button.click(
        fn=handle_submit_api,
        inputs=[city_input, gr.State(None), job_id_state],
        outputs=[result_output, download_output, job_id_state]
    )
    csv_event = csv_button.click(
        fn=handle_submit_api,
        inputs=[gr.State(""), csv_input, job_id_state],
        outputs=[result_output, download_output, job_id_state]
    )
    
    stop_button.click(fn=None, inputs=None, outputs=None, cancels=[city_event, csv_event])
    
    # demo.load(
    #     fn=handle_submit_api,
    #     js="() => sessionStorage.getItem('current_job_id')", # 페이지 로드 시 이 JS 함수를 먼저 실행
    #     inputs=[gr.State(""), gr.State(None), job_id_state], # JS 함수의 반환값이 이 컴포넌트로 들어감
    #     outputs=[job_id_state]
    # )
    # 3) 페이지 로드시: 세션에 있던 job_id를 hidden state에만 채워 넣음 (파이썬 함수 호출 X)
    
    job_id_state.change(
        fn=None,
        inputs=job_id_state,
        outputs=[job_id_state],  # 출력 1개만
        js="""(job_id) => {
        if (job_id) sessionStorage.setItem('current_job_id', job_id);
        else sessionStorage.removeItem('current_job_id');
        return job_id ?? "";  // null/undefined 금지
        }"""
    )
    
    # (2) 그와 별개로, 값이 바뀌면 폴링을 시작/재개 (파이썬 전용)
    job_id_state.change(
        fn=handle_submit_api,
        inputs=[gr.State(""), gr.State(None), job_id_state],
        outputs=[result_output, download_output, job_id_state]
    )

    
    demo.load(
        fn=None,
        inputs=None,
        outputs=[job_id_state],                         # 출력 1개
        js="() => sessionStorage.getItem('current_job_id') || ''"  # 반환도 1개
    )


if __name__ == "__main__":
    demo.queue().launch(server_name="127.0.0.1", share=True)