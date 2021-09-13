import logging
import os
import os.path
import time
from uuid import uuid4

import aiofiles
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi_utils.tasks import repeat_every

BASE_DIR = os.getenv('FTS_BASE_DIR', './tmp')
DOWNLOAD_EXPIRE_SECONDS = int(os.getenv('FTS_DOWNLOAD_EXPIRE_SECONDS', 60 * 3 ))  # 3 minutes
FILE_DELETE_TASK_INTERVAL = int(os.getenv('FTS_FILE_DELETE_TASK_INTERVAL', 10 ))
FILE_DELETE_INTERVAL = int(os.getenv('FTS_FILE_DELETE_INTERVAL', 60 * 5 ))  # 5 minutes
FILE_BUFFER_SIZE = int(os.getenv('FTS_FILE_BUFFER_SIZE', 1024 * 64 ))  # 64K Buffer

logger = logging.getLogger('uvicorn.error')

app = FastAPI()


@app.post('/upload/')
async def upload(file: UploadFile = File(...)):
    uid = uuid4()
    path = os.path.join(BASE_DIR, f'{uid}_{file.filename}')

    async with aiofiles.open(path, 'wb') as f:
        while content := await file.read(FILE_BUFFER_SIZE):
            await f.write(content)
        await f.close()

    return HTMLResponse(content=f'''<a href=/download/{uid}_{file.filename}>download</a>''', status_code=200)


@app.get('/download/{file_id}')
async def download(file_id):
    path = os.path.join(BASE_DIR, file_id)

    if not os.path.isfile(path):
        return {'result': '해당 파일이 존재하지 않습니다.'}

    mtime = os.path.getmtime(path)

    if mtime < time.time() - DOWNLOAD_EXPIRE_SECONDS:
        return {'result': '다운로드 가능 시간이 만료되었습니다.'}

    return FileResponse(path)


@app.on_event('startup')
def on_start():
    if not os.path.exists(BASE_DIR):
        os.mkdir(BASE_DIR)

    logger.info('Load Environment Settings')
    logger.info(f'BASE_DIR := {BASE_DIR}')
    logger.info(f'DOWNLOAD_EXPIRE_SECONDS := {DOWNLOAD_EXPIRE_SECONDS}')
    logger.info(f'FILE_DELETE_TASK_INTERVAL := {FILE_DELETE_TASK_INTERVAL}')
    logger.info(f'FILE_DELETE_INTERVAL := {FILE_DELETE_INTERVAL}')
    logger.info(f'FILE_BUFFER_SIZE := {FILE_BUFFER_SIZE}')


@app.on_event('startup')
@repeat_every(seconds=FILE_DELETE_TASK_INTERVAL)
def remove_expired_file_task():
    for f in os.listdir(BASE_DIR):
        path = os.path.join(BASE_DIR, f)

        if not os.path.isfile(path):
            continue

        mtime = os.path.getmtime(path)

        if mtime < time.time() - FILE_DELETE_INTERVAL:
            os.remove(path)
            logger.info(f'{f} is expired, delete.')
