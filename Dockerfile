FROM python:3.11.0

ENV TOKENIZERS_PARALLELISM=false

COPY requirements.txt ./

RUN pip install -r requirements.txt

WORKDIR /app

COPY ./ ./

EXPOSE 8000

CMD ["python", "imean.py"]