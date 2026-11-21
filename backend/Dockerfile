FROM public.ecr.aws/lambda/python:3.11

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .
RUN pip install --no-cache-dir numpy==2.2.6 && \
    pip install --no-cache-dir -r requirements.txt

COPY parsers.py lambda_handler.py ${LAMBDA_TASK_ROOT}/

ENV AWS_REGION=ap-south-1
ENV S3_BUCKET=doc-markdown-poc-mumbai
ENV DDB_TABLE=DocMarkdownMetadataPoc

CMD ["lambda_handler.handler"]