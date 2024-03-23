FROM --platform=linux/amd64 python:3.9

WORKDIR /dir

COPY ./requirements.txt /dir/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /dir/requirements.txt


COPY ./static/ /dir/static/
COPY ./main.py /dir/

EXPOSE 443

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "443",  "--ssl-keyfile=/etc/tls/tls.key", "--ssl-certfile=/etc/tls/tls.crt"]