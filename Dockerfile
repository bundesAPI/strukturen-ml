FROM public.ecr.aws/lambda/python:3.9

COPY *.py requirements.txt model-last/ ./

RUN python3.9 -m pip install poetry
RUN python3.9 -m poetry export --without-hashes -f requirements.txt --output requirements.txt
RUN python3.9 -m pip install -r requirements.txt -t .
# Command can be overwritten by providing a different command in the template directly.
CMD ["lambda.handler"]