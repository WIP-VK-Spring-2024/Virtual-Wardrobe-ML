FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04
# already has python 3.10.12

# Set the working directory
RUN mkdir /usr/src/app
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    ca-certificates \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python and pip
RUN apt-get update && apt-get install -y python3-pip

RUN pip3 install -U pip 


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8


RUN pip3 install torch==2.0.1+cu118 torchvision==0.15.2+cu118 -f https://download.pytorch.org/whl/cu118/torch_stable.html


RUN pip3 install 'git+https://github.com/facebookresearch/detectron2@main#subdirectory=projects/DensePose'

COPY requirements.txt /usr/src/app/

RUN pip3 install -r requirements.txt    

# commented to guarantee sync volume changes
COPY . /usr/src/app/
