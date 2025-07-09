# Используем официальный базовый образ с поддержкой Miniconda
FROM continuumio/miniconda3:latest

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей
COPY environment.yml ./

# Устанавливаем зависимости через conda
RUN conda env create -f environment.yml

# Активируем окружение по умолчанию
SHELL ["/bin/bash", "-c"]
ENV PATH /opt/conda/envs/llm-tg-bot/bin:$PATH

# Копируем исходный код проекта
COPY . .

# Устанавливаем python-dotenv для поддержки .env
RUN conda install -n llm-tg-bot python-dotenv

# Открываем стандартный порт (если нужен)
EXPOSE 8080

# Копируем .env.example как .env, если .env не задан (Railway/облако)
RUN [ ! -f .env ] && cp .env.example .env || true

# Запуск бота
CMD ["python", "-m", "src"] 