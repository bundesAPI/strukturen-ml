try:
    import unzip_requirements
except ImportError:
    pass
from mangum import Mangum
from main import app

@app.get("/",  tags=["Endpoint Test"])
def main_endpoint_test():
    return {"message": "Just another strukturen API! [orgchart-ml]"}

handler = Mangum(app)
