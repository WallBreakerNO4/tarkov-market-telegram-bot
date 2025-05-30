FROM python:3.12-slim
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple --no-cache-dir -r requirements.txt 
COPY . /app
CMD ["python", "bot.py"]