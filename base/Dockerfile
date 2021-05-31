FROM osgeo/gdal

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

# Get GDAL dependencies (https://stackoverflow.com/a/46880451)
RUN apt-get update && apt-get install -y \
  binutils    \
  git         \
  gdal-bin    \
  python3-pip

RUN pip3 install Flask gunicorn

ADD ./requirements.txt /base/requirements.txt
RUN pip3 install -r /base/requirements.txt