FROM public.ecr.aws/lambda/python:3.8

COPY *.py ${LAMBDA_TASK_ROOT}
RUN ls
COPY requirements.txt ${LAMBDA_TASK_ROOT}
COPY model-last/ ${LAMBDA_TASK_ROOT}/model-last/
RUN ls ${LAMBDA_TASK_ROOT}
RUN yum update && \
  yum install -y \
  g++ \
  make \
  cmake \
  unzip \
  libcurl4-openssl-dev\
  gcc \
  gcc-c++
RUN python3.8 -m pip install -r requirements.txt -t ${LAMBDA_TASK_ROOT}
RUN python3.8 -m pip install awslambdaric --target ${LAMBDA_TASK_ROOT}
# Command can be overwritten by providing a different command in the template directly.
CMD ["lambda_function.handler"]