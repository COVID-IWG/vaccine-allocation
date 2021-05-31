# use the official lightweight Python image (https://hub.docker.com/_/python)
FROM python:3.9-slim

# allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True
# debian apt settings (https://serverfault.com/a/1035343)
ENV DEBIAN_FRONTEND noninteractive

# get GDAL dependencies (https://stackoverflow.com/a/46880451)
RUN apt-get update &&  \
    apt-get install -y \
        apt-utils    \ 
        binutils     \
        git          \
        gdal-bin     \
        libgdal-dev  \
        python3-gdal \
        python3-pip

# set up virtual environment (https://pythonspeed.com/articles/activate-virtualenv-dockerfile/)
ENV VIRTUAL_ENV=/env
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# install non-app requirements
RUN pip3 install Flask gunicorn

# install app-specific requirements
ADD ./requirements.txt /base/requirements.txt
RUN pip3 install -r /base/requirements.txt