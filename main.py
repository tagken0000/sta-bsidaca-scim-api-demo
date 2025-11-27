import os
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import requests
 
# ---------- 設定（環境変数） ----------
STA_API_BASE = os.getenv("STA_API_BASE", "")
STA_TENANT_CODE = os.getenv("STA_TENANT_CODE", "")
STA_API_KEY = os.getenv("STA_API_KEY", "")
BSIDCA_WSDL_URL = os.getenv("BSIDCA_WSDL_URL", "")
 
def sta_headers():
    # STAのAPIキーで認証（Bearer）
    return {"Authorization": f"Bearer {STA_API_KEY}", "Content-Type": "application/json"}
 
# ---------- アプリ本体 ----------
app = FastAPI()
 
# 静的ファイル（フロントUI）を公開
app.mount("/static", StaticFiles(directory="static"), name="static")
 
# トップページ（index.html）を返す
@app.get("/")
def index():
    return FileResponse("static/index.html")
 
# 1) SCIMでSTAユーザー作成
@app.post("/api/create-user")
def create_user(user_id: str, given_name: str, family_name: str, email: str):
    if not (STA_API_BASE and STA_TENANT_CODE and STA_API_KEY):
        raise HTTPException(status_code=500, detail="STAの設定が未入力です。環境変数を確認してください。")
 
    # SCIM Usersエンドポイント（テナントコード付き）
    # 参考：STA APIリファレンス（SCIM/RESTの使用方法とAuthorize手順）[1](https://thalesdocs.com/sta/api/)
    scim_url = f"{STA_API_BASE}/v2/scim/tenants/{STA_TENANT_CODE}/Users"
    payload = {
        "userName": user_id,
        "name": {"givenName": given_name, "familyName": family_name},
        "emails": [{"value": email, "type": "work", "primary": True}],
        "active": True
    }
    r = requests.post(scim_url, headers=sta_headers(), json=payload, timeout=30)
    if r.status_code not in (200, 201):
        raise HTTPException(status_code=500, detail=f"SCIMユーザー作成失敗: {r.text}")
    return r.json()
 
# 2) BSIDCAでMobilePASSを割当＆エンロールメール送信
@app.post("/api/enroll-token")
def enroll_token(user_id: str):
    if not BSIDCA_WSDL_URL:
        raise HTTPException(status_code=500, detail="BSIDCAのWSDL URLが未入力です。環境変数を確認してください。")
 
    # ここではWSDLの呼び出しを簡略化し、デモ用の成功レスポンスを返します。
    # 実際にはzeepでclient.service.<メソッド>を呼びます（テナントのWSDL定義に依存）。
    # 参考：BSIDCA WSDL APIはユーザー／トークン管理のSOAPメソッド群を提供。[1](https://thalesdocs.com/sta/api/)
    try:
        # 実運用では、以下のような流れ：
        # from zeep import Client
        # client = Client(wsdl=BSIDCA_WSDL_URL)
        # client.service.AssignTokenToUser(userId=user_id, tokenType="MobilePASS")
        # client.service.SendEnrollmentEmail(userId=user_id)
        # ここではデモのため固定の成功メッセージを返します。
        return {"status": "ok", "message": f"ユーザー {user_id} へMobilePASS割当＆エンロールメール送信（仮）"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BSIDCA呼び出し失敗: {e}")
