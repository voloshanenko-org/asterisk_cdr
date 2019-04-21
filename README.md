Bionova PBX call logs viewer


Local build:

pip3 install virtualenv
virtualenv -p python3 venv
source venv/bin/activate

Docker build:

PROD:
1. Set env variable
2. Run docker-compose
#docker-compose up -d
3. To rebuild run with --build flag

 
DEV:
1. Edit env.dev file to set real values for DB host
#vim env.dev
2. Source env file and run docker-compose
#source env.dev && docker-compose -f docker-compose.dev.yml up
3. to rebuild - just rerun same container - as code mounted as folder to container
