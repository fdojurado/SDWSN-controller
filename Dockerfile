FROM python:3.9
COPY . /app
WORKDIR /app/controller
# RUN pip3 install plac
# RUN pip3 install -r requirements.txt
# RUN python -m pip install --upgrade pip
RUN pip install pathlib
RUN pip3 install .
CMD python3 bin/serial-controller

# Commands to build and run
# docker build -t elise-2 .
# docker run elise-2 
