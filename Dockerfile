FROM python:3.10-slim-buster

EXPOSE 5000

COPY  requirements.txt /requirements.txt
RUN apt update && \
    apt install -y gcc libmariadbclient-dev && \
    pip3 install --no-cache-dir -r requirements.txt && \
    apt purge -y gcc libmariadbclient-dev && \
    apt autoremove -y
COPY app.py config.py app/
COPY app app/app

WORKDIR app/
CMD ["python3", "app.py"]
