Отчётности ООО "Аргон" и "МЭЙЛ.РУ ФИНАНС" не представлены в подготовленной заранее базе данных. Если вы хотите задавать вопросы по ним -- необходимо загрузить их через интерфейс бота или с помощью отправки POST-запроса /load_pdf.
# Инструкция по запуку:
## Шаг 1: клонировать репозиторий 

```bash
https://github.com/ai-integration-company/Genesis-Hack-RAG.git
```
```bash
cd Genesis-Hack-RAG 
```
## Шаг 2: вставить telegram api token Вашего бота в telegram_bot/.env API_TOKEN="Ваш токен"
## Шаг 3: поднять сервер (ПОДОЖДИТЕ 5-9 минут пока в Chroma загрузятся вектора предоставленных файлов)
```bash
docker-compose build
```
```bash
docker-compose up
```
## Шаг 4: зайдите в бота (НАПОМИНАЮ про 5-9 минут пока в Chroma загрузятся вектора предоставленных файлов)

## Шаг 5: задайте вопрос или отправьте файл в формате pdf. Для очистки истории запросов нажмите кнопку в меню бота. При добавлении pdf загружайте файлы в формате по одному, присылайте их отдельным сообщением.

# СОВЕТ: не загружать слишком большие файлы (они будут долго обрабатываться). Желательно 3-4 страницы. Отправлять данные такого же формата как и предостваленные: машинописные или сканы.
