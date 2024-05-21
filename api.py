from fastapi import FastAPI, Request, Response, BackgroundTasks
from engine import Engine
from train import train_ai
from config import *
from util import *
from etl import *
import uvicorn

app = FastAPI()
engine = Engine()

@app.get('/')
async def root():
    return 'Hello BoatRace AI!'

@app.post('/predict')
async def predict(request: Request, response: Response, bk_tasks: BackgroundTasks):
    data = await request_to_json(request)
    if data is None: return json_response(200, -1, 'Invalid request params.')

    pred = engine.predict('raw', data, None)

    if pred['code'] == 0:
        return json_response(200, 0, {
            'predict': pred['predict'], 'best': pred['best'], 'why': pred['why']
        })
    else:
        return json_response(200, -2, { 'why': pred['why'] })

@app.post('/refresh_data')
async def refresh_data(request: Request, response: Response, bk_tasks: BackgroundTasks):
    blind_update(engine.id_data, engine.game_data, engine.course_data)
    engine.refresh_data()

    return json_response(200, 0, 'ok')

@app.post('/train')
async def train(request: Request, response: Response, bk_tasks: BackgroundTasks):
    bk_tasks.add_task(train_proc)

    return json_response(200, 0, 'ok')

def train_proc():
    prepare_train_data()
    train_ai(engine.net, 1, False, True)

if __name__ == '__main__':
    uvicorn.run(app = "api:app", host = '0.0.0.0', port = 8000, reload = False)
