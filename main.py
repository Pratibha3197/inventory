from typing import List
import pandas as pd
import re
from fastapi import FastAPI, Request, Depends,Form, HTTPException
from starlette.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from model import UserSchema, UserLoginSchema
from routes.auth import signJWT
from fastapi import FastAPI, Body
from fastapi.templating import Jinja2Templates
import time
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.responses import RedirectResponse, HTMLResponse
from starlette.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import logging
from routes import EOQ, ABC, salesprice, salesquantity, Realtimeinventory
# from mangum import Mangum

# # Adjust logging level for multipart.multipart logger
logging.getLogger('multipart.multipart').setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)


InventoryModel = FastAPI()
# handler=Mangum(InventoryModel)


templates = Jinja2Templates(directory="templates")
InventoryModel.mount("/static",StaticFiles(directory="static",html=True),name="static")


@InventoryModel.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


def check_user(data: UserLoginSchema):
    df = pd.read_csv("user.csv")
    for index, row in df.iterrows():
        if row['email'] == data.email and row['password'] == data.password:
            df.loc[index, 'user_activity'] = time.time()
            df.to_csv("user.csv", index=False, header=True)
            return True
    return False

def check_email(email):
    pat = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.match(pat, email):
        return "Valid Email"
    else:
        return "Invalid Email"


# def check_name(name):
#     regex_name = re.compile(r'^(Mr\.|Mrs\.|Ms\.) ([a-z]+)( [a-z]+)*( [a-z]+)*$',
#                             re.IGNORECASE)
#     res = regex_name.search(name)
#     if res:
#         return "Valid Name"
#     else:
#         return "Invalid Name"

def check_name(name):
    regex_name = re.compile(r'^[a-zA-Z\s\-\'\.]+$')
    res = regex_name.search(name)
    if res:
        return "Valid Name"
    else:
        return "Invalid Name"
    
def load_users():
    return pd.read_csv("user.csv")

@InventoryModel.post('/signup', tags=['user'])
def user_signup(user: UserSchema = Body(default=None)):
    user_dict = user.dict()
    user_df = pd.DataFrame(user_dict, index=[0])
    user_df['user_activity'] = time.time()
    
    if check_email(user_dict['email']) == 'Valid Email':
        if check_name(user_dict['fullname']) == 'Valid Name':
            user_df.to_csv('user.csv', mode='a', header=False, index=False)
            jwt_token = signJWT(user_dict['email'])  # Pass email only
            return JSONResponse(content={"token": jwt_token})
        else:
            raise HTTPException(status_code=400, detail="Invalid Name")
    else:
        raise HTTPException(status_code=400, detail="Invalid Email")


@InventoryModel.post('/login', tags=["user"])
def user_login(user: UserLoginSchema = Body(default=None)):
    if check_user(user):
        jwt_token = signJWT(user.email)
        return JSONResponse(content={"token": jwt_token})
    else:
        raise HTTPException(status_code=401, detail="Invalid login details")
#Include routers
InventoryModel.include_router(EOQ.router,tags= ["InventoryAnalysis"])
InventoryModel.include_router(ABC.router,tags= ["InventoryAnalysis"])
InventoryModel.include_router(salesprice.router,tags= ["InventoryAnalysis"])
InventoryModel.include_router(salesquantity.router,tags= ["InventoryAnalysis"])
InventoryModel.include_router(Realtimeinventory.router,tags= ["InventoryAnalysis"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(InventoryModel, host="127.0.0.1", port=8000)


    
