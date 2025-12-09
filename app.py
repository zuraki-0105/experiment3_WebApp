@app.get("/")
def hello():
    return {"msg": "hello"}
