FROM python:3.7-alpine

EXPOSE 5000

RUN pip install --upgrade pip

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN apk add --update --no-cache libstdc++ mariadb-connector-c-dev \
	&& apk add --no-cache --virtual .build-deps \
		mariadb-dev \
		gcc \
		musl-dev \
                openssl-dev \
                libffi-dev \
	&& pip install mysqlclient \
        && pip install -r requirements.txt \
	&& apk del .build-deps

COPY . /app

CMD ["python", "./app.py"]
