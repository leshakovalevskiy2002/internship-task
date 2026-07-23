import os

import uvicorn

if __name__ == "__main__":
    is_dev = os.getenv("MODE", "prod") == "dev"

    uvicorn.run("app.config.app:app", host="0.0.0.0", port=7999, reload=is_dev)
