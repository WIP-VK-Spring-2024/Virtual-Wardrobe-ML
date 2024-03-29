# Model api

## Fast setup
Предварительно нужно создать файл ```.env``` в корне проекта по шаблону .env.example

Далее надо освободить порт 5432, используемый обычно Postgres, после чего запускаем контейнер:

### FastAPI and RabbitMQ
```shell
docker network create shared-api-network
docker-compose up -d --build
```
### All model runners for queing tasks
```shell
docker compose -f docker-compose-model.yml up -d --build --force-recreate
```

## ML usage
> За неимением времени на разработку в проекте используется requirements.txt для запуска ML части. В планах его перенести в pyproject.toml.

Чтобы ml заработал нужно скачать веса. Для этого скачиваем архив с весами (ссылку можно попросить у @KOTOBOPOT). Его содержимое распаковываем в папку ML__WEIGHTS_PATH (переменная в .env). Указанные операции можно сделать при помощи следующих команд:

```shell
wget /link/to/weights/archieve -O weights.zip \
&& source .env \
&& unzip weights.zip -d $ML__WEIGHTS_PATH\
&& rm weights.zip
```

Classes for working has folowing view:
1) __Clothes Preprocessing__: app/pkg/ml/try_on/preprocessing/aggregator.py - class: ClothProcessor. method: consistent_forward(image_bytes)
<br>Clothes processing launches when user has uploded cloth image

2) __Human Preprocessing__: app/pkg/ml/try_on/preprocessing/aggregator.py - class: HumanProcessor. method: consistent_forward(image_bytes)
<br>Human processing launches when user has uploded human image

3) __Try on__: app/pkg/ml/try_on/lady_vton.py  class: LadyVtonAggregator. method: \_\_call\_\_(dict)
<br>Try on processing launches when user has requested to try on. Input dict format is:
```
{
"image_human_orig":io.BytesIO,  # - image with human
"parsed_human":io.BytesIO,  # - image with parsed human. 
"keypoints_json":io.BytesIO # human keypoints json
"cloth":io.BytesIO # cloth (without background) image bytes
"category":str, # one of ['dresses', 'upper_body','lower_body']
}
```
Keys from dict above corresponds with output keys from 1) and 2) methods.

P.S. It's recommended to init instances once in each class above. Initialization process can require more time, than image processing. 

## Launch dev container
### Dockerfile  
```shell
docker build -t dev_virt_ward:latest -f docker/model/Dockerfile_dev .
docker run -id --rm --gpus all -v .:/usr/src/app/ --name virt_ward_dev dev_virt_ward:latest
```
### Docker compose
```
docker compose -f docker-compose-dev.yml up -d --build --force-recreate
```

