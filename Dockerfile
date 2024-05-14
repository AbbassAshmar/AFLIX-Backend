#create a docker image in a docker file, the docker image 
#contains the instructions(libraries,requirements...)to be 
#executed to create a functioning docker cont.
#docker containers are a runing docker images isolating an app


#use a docker base image to write on top of (add instructions to)
FROM python:3-alpine
# set the workdirectory and if not found, create it (created in the container only not on the host machine)
WORKDIR /usr/src/app/backend
COPY requirements.txt .

# install requirements in the container work directory
run pip install -r requirements.txt

# copy from host machine to the container file system (a virtual file system that is created on top of the host system)
COPY . .

# to run psql, docker-compose exec <service name of database> psql -U <postgres server Name>
ENV PATH="$PATH:C:\Program Files\PostgreSQL\15\data"
# expose the port to be accessed by other containers
EXPOSE 8000 
CMD ["python3","manage.py","runserver", "0.0.0.0:8000"]

# run docker build -t <container-name> <path of the docker file> to build the image

# to run a container based on the built image , use docker run <image-name>