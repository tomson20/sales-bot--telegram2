FROM python:3.10-slim

WORKDIR /app

# საჭირო სისტემური პაკეტები gspread-ისთვის და Cython პროექტებისთვის
RUN apt-get update && apt-get install -y gcc libpq-dev curl

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000

CMD ["python", "main.py"]
