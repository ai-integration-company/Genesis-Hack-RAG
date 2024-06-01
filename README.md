Create a `.env` file in root repository from envexample.
Create a `.env` file in each directory in src directory from env-example repository from env-example.

Run next code in terminal:

```bash
docker exec -it postgres psql -U postgres -d genesis -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker exec -it vector python /vector/make_table.py
```

```
API_TOKEN=YOUR_TOKEN
```
