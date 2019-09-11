FROM continuumio/miniconda3

COPY . code/
WORKDIR code/

RUN apt-get update
RUN apt-get install -y curl g++ make
RUN ./install-spatialindex.sh
RUN pip install -r requirements.txt
RUN ./get_data.sh

ENTRYPOINT jupyter notebook --ip 0.0.0.0 --no-browser --allow-root
