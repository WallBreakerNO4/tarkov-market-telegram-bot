FROM python:3.14-slim
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple --no-cache-dir -r requirements.txt 
#COPY . /app
COPY bot.py /app/bot.py
COPY libs /app/libs
CMD ["python", "bot.py"]