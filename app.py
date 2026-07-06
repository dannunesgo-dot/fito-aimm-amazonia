from fastapi import FastAPI

app = FastAPI()

@app.get("/api/test")
def api_test():
    return {"ok": True}