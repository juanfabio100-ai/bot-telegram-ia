# Imagem base Python
FROM python:3.11-slim

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho
WORKDIR /app

# Copia requirements primeiro (cache eficiente)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto
COPY . .

# Cria pastas necessárias
RUN mkdir -p data logs

# Porta exposta
EXPOSE 5000

# Comando para rodar
CMD ["python", "main.py"]
