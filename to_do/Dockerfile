FROM ubuntu:18.04

RUN apt-get update && \ apt-get install -y build-essential \ python3 \ python3-dev \ python3-pip

COPY . app

RUN pip3 install uwsgi && \ pip3 install -r app/requirement.txt

EXPOSE 8000

CMD ["uwsgi", "--ini", "app/uwsgi.ini"]

docker build -t to_do .

docker run to_do