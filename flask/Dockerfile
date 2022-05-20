# Use the Python3.7.2 image
FROM python:3.10

# Set the working directory to /app
WORKDIR /app

EXPOSE 5000

# Copy the current directory contents into the container at /app 
ADD . /app
# Install the dependencies
RUN pip install -r requirements.txt

# run the command to start uWSGI
CMD ["uwsgi","--ini", "app.ini"]

