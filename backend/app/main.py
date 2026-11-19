from fastapi import FastAPI


app = FastAPI(title="ZeroWasteNet")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "ZeroWasteNet API"}
