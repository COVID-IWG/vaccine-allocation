# Use pre-packaged Python environment 
FROM gcr.io/adaptive-control/vaccine-allocation-base

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . /app

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Timeout is set to 0 to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
# ENTRYPOINT ["gunicorn" "--bind" ":$PORT" "--workers" "1" "--threads 8" "--timeout" "0" "main:app"]
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
